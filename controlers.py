import numpy as np
from tools import normalize, sign
from math import ceil


class Controler:

    def __init__(self, sat=None):
        self.G = 6.6743015 * 10 ** -11

        self.reach_geo = None
        self.reach_sync = None
        self.do_homhann = None

    def load(self, sat):
        if not sat is None:
            self.sat = sat
            self.planet = self.sat.planet_ref
            self.simulator = self.sat.simulator

    def geo_speed(self, radius):
        """
        Retourne la vitesse nécessaire pour maintenir l'orbite GEO au rayon demandé

        :param radius: (float) rayon autour du centre de l'astre (en m)
        :return: (float) vitesse tangentielle (en m/s)
        """
        return np.sqrt(self.G * self.planet.mass / radius)

    def get_period(self):
        """
        Calcule la période orbitale du satellite.

        :return: (float) la période orbitale (en s^-1)
        """
        # Calcul de la distance entre la position du satellite et la position de référence de la planète
        distance = np.linalg.norm(self.sat.x - self.planet.x)

        # Calcul de la norme (magnitude) de la vitesse du satellite
        vitesse = np.linalg.norm(self.sat.v)

        # Calcul de la période
        periode = 2 * np.pi * (distance / vitesse)

        return periode

    def get_homhann_transfert_time(self, r1, r2):
        return 1 / 2 * np.sqrt(4 * np.pi ** 2 / self.G / self.planet.mass * ((r1 + r2) / 2) ** 3)

    def power_for_synchronize_rotation(self, axe=2):
        power = - self.sat.v_ang[axe] * self.sat.inertia[axe] / self.simulator.dt
        if power == 0:
            return 0, 0
        for thruster in self.sat.thrusters:
            T = thruster.torque_max[axe]
            if T != 0:
                if sign(power) == sign(T):
                    power /= thruster.torque_max[axe]
                    n = ceil(power)
                    return {'power': power, 'n': n, 'thruster': thruster.name}

    def synchronize(self, args={}):
        self.reach_sync = self.power_for_synchronize_rotation(axe=2)
        self.reach_sync['step'], self.reach_sync['iteration'] = 'stop', 0
        self.sat.get(self.reach_sync['thruster']).on(power=self.reach_sync['power'])
        print(f"   | ctr: start to stop rotation")

    def homhann(self, args={'radius': 0}):
        r1, r2 = self.sat.get_radius(), args['radius']
        v = np.sqrt(np.dot(2 * self.G * self.planet.mass, np.array([1 / r1, 1 / r2]) - 1 / (r1 + r2)))
        self.do_homhann = self.power_for_speed(speed=v[0] - self.sat.get_speed())
        self.do_homhann['radius'] = r2
        if self.do_homhann is None:
            print(f"   ctr: impossible to reach an elliptical orbit")
        else:
            self.do_homhann['time'] = self.get_homhann_transfert_time(r1=r1, r2=r2)
            data = self.power_for_rotation(period=-2 * self.do_homhann['time'])
            self.do_homhann['stop_at'] = self.do_homhann['time'] + self.simulator.time
            # power_already_in = Power "déjà comprise dans la alpha_point", donc à ne pas ajouter
            power_already_in = self.power_for_rotation(period=self.get_period())['power']
            if data is None:
                print(f"   ctr: impossible to reach an elliptical orbit")
            else:
                self.sat.get(data['thruster']).on(power=-(data['power'] - power_already_in))
                self.do_homhann['rot'] = data
                self.sat.get(self.do_homhann['thruster']).on(power=self.do_homhann['power'])
                self.do_homhann['step'], self.do_homhann['iteration'] = 'reach_elliptic', 0

    def power_for_speed(self, speed, niteration=1, direction=(1, 0, 0)):
        """
        Retourne la puissance (de 0% à 100%) à appliquer au thruster précisé en sortie, durant niteration de dt sec,
        afin d'augmenter sa vitesse de speed dans la direction souhaitée

        :param speed: (float) Écart de vitesse à ajouter (speed = v_fin - v_init)
        :param dt: (float) Pas de temps discrétisé constant durant la mise en puissance des thruster (en sec)
        :param niteration: (int) Nombre d'iration souhaite. Attention: Celui-ci peut finalement augmenter, si le nombre
                                 d'itération souhaité n'est pas suffisant
        :param direction: (1D array, 3 values) Vecteur directeur normalisé de la direction de la vitesse souhaité
        :return: (dict) {'power': (float) Puissance de 0% à 100% du thruster,
                         'niteration': Nombre d'itération nécessaire à la rotation,
                         'thruster_name': Nom du thruster à activer.
        """
        dt = self.simulator.dt
        for n in range(niteration, 20 * niteration):  # Essaie en n itérations, sinon essaie avec n+1, ...
            for thruster in self.sat.thrusters:  # Essaie tous les thrusters possibles
                # Calcul de la valeur maximale de poussée du thruster dans la direction souhaitée
                thrust_max = thruster.thrust_max * np.dot(thruster.direction, direction)
                if thrust_max != 0:
                    # Calcul de la puissance nécessaire pour atteindre la vitesse souhaitée
                    power = self.sat.mass * speed / (n * dt * thrust_max)
                    if 0 <= power <= 1.:  # Vérification de la plage de puissance valide (0% à 100%)
                        return {'power': power, 'n': n, 'thruster': thruster.name}

    def power_for_rotation(self, period, niteration=1, axe=2):
        """
        Retourne la puissance (de 0% à 100%) à appliquer au thruster précisé en sortie, durant niteration de dt sec,
        afin de tourner avec la période souhaité autour de l'axe désiré.

        :param period: (float) Durée de la révolution du satellite (en sec).
                               Note: Pour une roration sens horaire, mettre une période négative pour changer de signe.
        :param dt: (float) Pas de temps discrétisé constant durant la mise en puissance des thruster (en sec)
        :param niteration: (int) Nombre d'iration souhaite. Attention: Celui-ci peut finalement augmenter, si le nombre
                                 d'itération souhaité n'est pas suffisant
        :param axe: (int in [0,1,2]) Indice de l'axe de rotation
        :return: (dict) {'power': (float) Puissance de 0% à 100% du thruster,
                         'niteration': Nombre d'itération nécessaire à la rotation,
                         'thruster_name': Nom du thruster à activer.
        """
        dt = self.simulator.dt
        for n in range(niteration, 10 * niteration):  # Essaie en n itérations, sinon essaie avec n+1, ...
            for thruster in self.sat.thrusters:     # Essaie tous les thrusters possibles
                if thruster.torque_max[axe] != 0:
                    # Calcul de la puissance nécessaire pour effectuer une rotation avec la période souhaitée
                    power = 2*np.pi * self.sat.inertia[axe] / (n * dt * period * thruster.torque_max[axe])

                    if 0 <= power <= 1.:            # Vérification de la plage de puissance valide (0% à 100%)
                        return {'power': power, 'n': n, 'thruster': thruster.name}

    def update(self, infos=True):
        """
        Met à jour les paramètres et l'état du satellite lors d'une mise à jour de l'orbite.

        :param infos: (bool) Indique si les informations doivent être affichées (par défaut True).
        """
        if not self.reach_geo is None:
            gamma = 10 ** -6  # power per meter
            ur, r = normalize(self.sat.x - self.planet.x), self.sat.get_radius()
            theta = np.arccos(np.dot(self.sat.ux, ur))
            power_stat = np.linalg.norm(self.sat.ag) * self.sat.mass / (self.sat.get('main').thrust_max * np.cos(theta))
            power_dyna = gamma * (self.reach_geo - r)
            self.sat.get('main').on(power=power_stat + power_dyna)

            # CHEAT :
            if r >= self.reach_geo:
                prev_r, prev_v = r, self.sat.get_speed()
                self.sat.x = self.reach_geo * ur
                self.sat.v = self.geo_speed(radius=self.reach_geo) * np.cross(-ur, np.array([0, 0, 1]))
                self.sat.get('main').off()
                self.reach_geo = None

                delta_r = abs(round(100 * (prev_r - self.sat.get_radius()) / prev_r, 2))
                delta_v = abs(round(100 * (prev_v - self.sat.get_speed()) / prev_v, 2))
                print(f"   | GEO orbit forced ({delta_r}% for position, {delta_v}% for speed)")
                print(f"     GEO orbit reached at {self.simulator.time} sec")
        if not self.reach_sync is None:
            if self.reach_sync['step'] == 'stop':
                if self.reach_sync['iteration'] == self.reach_sync['n']:
                    self.sat.get(self.reach_sync['thruster']).off()
                    self.reach_sync = {'step': 'wait', 'epsilon': 0.01, 'period': self.get_period()}
                    print(f"   | ctr: wait to synchronize rotation")
                else:
                    self.reach_sync['iteration'] += 1
            if self.reach_sync['step'] == 'wait':
                angle = np.arccos(np.dot(normalize(self.sat.x - self.planet.x)[0], self.sat.ux[0]))
                if np.pi / 2 * (1 - self.reach_sync['epsilon']) < angle < np.pi / 2 * (1 + self.reach_sync['epsilon']):
                    self.reach_sync = self.power_for_rotation(period=self.reach_sync['period'])
                    self.reach_sync['step'], self.reach_sync['iteration'] = 'sync', 0
                    self.sat.get(self.reach_sync['thruster']).on(power=self.reach_sync['power'])
            if self.reach_sync['step'] == 'sync':
                if self.reach_sync['iteration'] == self.reach_sync['n']:
                    self.sat.get(self.reach_sync['thruster']).off()
                    print(f"   | ctr: finish to synchronize rotation")
                    self.reach_sync = None
                else:
                    self.reach_sync['iteration'] += 1
        if not self.do_homhann is None:
            if self.do_homhann['step'] == 'reach_elliptic':
                if self.do_homhann.get('rot'):
                    if self.do_homhann['rot']['n'] == self.do_homhann['iteration']:
                        self.sat.get(self.do_homhann['rot']['thruster']).off()
                if self.do_homhann['n'] == self.do_homhann['iteration']:
                    self.do_homhann['step'] = 'on_elliptic'
                    print(f"   | elliptical orbit reached   ({self.simulator.time} sec)")
                    self.sat.get(self.do_homhann['thruster']).off()
                else:
                    self.do_homhann['iteration'] += 1
            if self.do_homhann['step'] == 'on_elliptic' and self.simulator.time >= self.do_homhann['stop_at']:
                r = self.do_homhann['radius']
                dv = self.geo_speed(radius=r) - self.sat.get_speed()
                self.do_homhann = self.power_for_speed(speed=dv)
                self.do_homhann['radius'] = r
                self.sat.get(self.do_homhann['thruster']).on(power=self.do_homhann['power'])
                self.do_homhann['step'], self.do_homhann['iteration'] = 'reach_geo', 0
            if self.do_homhann['step'] == 'reach_geo':
                if self.do_homhann['iteration'] == self.do_homhann['n']:
                    self.sat.get(self.do_homhann['thruster']).off()

                    # CHEAT :
                    ur = normalize(self.sat.x - self.planet.x)
                    self.sat.x = self.do_homhann['radius'] * ur
                    self.sat.v = self.geo_speed(radius=self.do_homhann['radius']) * np.cross(-ur, np.array([0, 0, 1]))

                    self.do_homhann = None
                    print(f"   | successful Homhann transfer")
                else:
                    self.do_homhann['iteration'] += 1







