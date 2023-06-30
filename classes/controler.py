import numpy as np
from classes.tools import normalize, sign, errors
from math import ceil


class Controler:

    def __init__(self, sat=None):
        """
        Classe Controler, intégré à un satellite, afin d'effectuer les commandes selon les instructions demandés
        par l'utilisateur

        :param sat: (class Satellite)
        """
        # Consatant de gravitation universelle
        self.G = 6.6743015 * 10 ** -11
        self.z = np.array([0, 0, 1])

        # États de contrôles actuels
        self.reach_geo = None   # Commande pous rejoindre une géo précise
        self.reach_sync = None  # Commande pour synchroniser la rotation avec la période orbitale
        self.do_homhann = None  # Commande pour réaliser un transfert d'Hohmann

        # Chargement des données du satellite
        self.load(sat=sat)

    def load(self, sat):
        """
        Charge le satellite désiré dans le controler

        :param sat: (class Satellite)
        :return: None
        """
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

        :return: (float) la période orbitale (en s)
        """
        # Calcul de la distance entre la position du satellite et la position de référence de la planète
        distance = np.linalg.norm(self.sat.x - self.planet.x)

        # Calcul de la norme (magnitude) de la vitesse du satellite
        vitesse = np.linalg.norm(self.sat.v)

        # Calcul de la période
        periode = 2 * np.pi * (distance / vitesse)

        return periode

    def get_homhann_transfert_time(self, r1, r2):
        """
        Calcule le temps nécessaire pour réaliser un transfert de Hohmann (demi-elliptique)

        :param r1: (float) Rayon GÉO de départ (en m)
        :param r2: (float) Rayon GÉO d'arrivée (en m)
        :return: (float) Temps de transfert (demi-période elliptique)
        """
        return 1 / 2 * np.sqrt(4 * np.pi ** 2 / self.G / self.planet.mass * ((r1 + r2) / 2) ** 3)

    def power_for_synchronize_rotation(self, axe=2):
        """
        Retourne la puissance (de 0% à 100%) à appliquer au thruster précisé en sortie, durant n iteration de dt sec,
        afin d'augmenter sa vitesse de rotation autour de l'axe souhaité

        :param axe: (int) Numéro de l'Axe de rotation (0 -> x, 1 -> y, 2 -> z)
        :return: (dict) {'power': (float) Puissance de 0% à 100% du thruster,
                         'n': Nombre d'itération nécessaire à la rotation,
                         'thruster': Nom du thruster à activer.
        """
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

    def geo(self, args={'radius': 0}):
        coef = 1 / self.simulator.dt * (self.sat.inertia[2] / self.sat.get('left').torque_max[2])
        self.reach_geo = {'radius': args['radius'], 'step': 'approach', 'switch_step': 0.80,
                          'gamma_1': 0.025, 'gamma_2': 0.02, 'speed': self.geo_speed(args['radius']),
                          'rot_pulse': 0.0015 * coef,
                          'epsilon': {'radius': 0.02, 'speed': 0.02, 'angle': 0.02}}
        print(f"   | ctr: phase 1 of geo reaching started")

    def takeoff(self, args={}):
        self.sat.istakingoff = True
        self.sat.get('main').on(power=0.90)

    def synchronize(self, args={}):
        """
        Ordonne au contrôleur de syncrhoniser la rotation avec la période orbitale, soit, sur une orbite GÉO :
            - Le vecteur ux poitera toujours vers le vecteur vitesse
            - Le vecteur +/- uy poitera toujours vers le centre de la planète de référence
        Créer le dictionnaire d'instruction reach_sync = {'power', 'n', 'thruster', 'step'}.
        La synchronisation est découpée en 3 étapes :
            - stop : Arrête la rotation du satellite (vitesse angulaier nulle)
            - wait : Attends que le vecteur +/- uy pointe vers le centre (à 1% prés)
            - sync : Ajuste la vitesse de rotation pour se synchroniser
        Cette méthode d'arrêt-resynchronisation n'est pas la plus optimale en terme de temps et de carburant, mais il
        s'agit de la moins complexe à implémenter.

        :param args: (dict, empty) Arguments optionel vide (nécessaire pour conserver un format unique)
        :return: (None)
        """
        self.reach_sync = self.power_for_synchronize_rotation(axe=2)
        self.reach_sync['step'], self.reach_sync['iteration'] = 'stop', 0
        self.sat.get(self.reach_sync['thruster']).on(power=self.reach_sync['power'])
        print(f"   | ctr: start to synchronize rotation")

    def homhann(self, args={'radius': 0}):
        """
        Ordonne au contrôleur de réaliser un transfert d'Hohmann du rayon actual au rayon radius désiré en argument.
        Les instructions de transfert sont d'abord calculées, vérifiées puis envoyées, si elles sont valides. Il faut
        donc que les instructions au départ ET à l'arrivée soient physiquement réalisables.
        Créer le dictionnaire d'instruction reach_sync = {'power', 'n', 'thruster', 'stop_at', 'radius', 'rot'}.
            Rot étant un dictionnaire contenant toutes les instructions de mise en rotation du satellite durant
            l'orbite elliptique.

        :param args: (dict) Donne le rayon d'arrivé du transfert. Le rayon de départ est le rayon actuel du satellite.
        :return: (None)
        """
        r1, r2 = self.sat.get_radius(), args['radius']
        v = np.sqrt(np.dot(2 * self.G * self.planet.mass, np.array([1 / r1, 1 / r2]) - 1 / (r1 + r2)))
        self.do_homhann = self.power_for_speed(speed=v[0] - self.sat.get_speed())
        if self.do_homhann is None:
            print(f"     ctr: impossible to reach an elliptical orbit")
        else:
            self.do_homhann['time'], self.do_homhann['radius'] = self.get_homhann_transfert_time(r1=r1, r2=r2), r2
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
        Retourne la puissance (de 0% à 100%) à appliquer au thruster précisé en sortie, durant n iteration de dt sec,
        afin d'augmenter sa vitesse de speed dans la direction souhaitée

        :param speed: (float) Écart de vitesse à ajouter (speed = v_fin - v_init)
        :param dt: (float) Pas de temps discrétisé constant durant la mise en puissance des thruster (en sec)
        :param niteration: (int) Nombre d'iration souhaite. Attention: Celui-ci peut finalement augmenter, si le nombre
                                 d'itération souhaité n'est pas suffisant
        :param direction: (1D array, 3 values) Vecteur directeur normalisé de la direction de la vitesse souhaité
        :return: (dict) {'power': (float) Puissance de 0% à 100% du thruster,
                         'n': Nombre d'itération nécessaire à la rotation,
                         'thruster': Nom du thruster à activer.
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
        Envoie les commandes au satellite selon les instructions demandés par l'utilisateur. Vérifie une à une les
        différentes instructions possibles, et les mets à jours si besoin.

        :param infos: (bool) Indique si les informations doivent être affichées (par défaut True).
        """
        if self.sat.islanded or self.sat.istakingoff:
            if self.sat.get_radius() > 1.01 * self.sat.planet_ref.radius:
                self.sat.islanded, self.sat.istakingoff = False, False
        # Instruction : Rejoindre l'orbite géo au rayon demandée
        if not self.reach_geo is None:
            if self.reach_geo['step'] == 'approach':
                T = (self.reach_geo['gamma_1'] + 1) * np.linalg.norm(self.sat.ag) * self.sat.mass
                self.sat.get('main').on(power=T / self.sat.get('main').thrust_max)
                if self.sat.get_radius()/ self.reach_geo['radius'] >= self.reach_geo['switch_step']:
                    self.reach_geo['step'] = 'reaching'
                    self.sat.get('left').on(power=self.reach_geo['rot_pulse'])
                    print(f"   | ctr: phase 2 of geo reaching started")
            elif self.reach_geo['step'] == 'reaching':
                self.sat.get('left').off()
                angle = np.arccos(np.dot(normalize(self.sat.x - self.planet.x)[0], self.sat.ux[0]))
                T = (self.reach_geo['gamma_2'] + 1) * np.linalg.norm(self.sat.ag)
                T -= self.sat.get_speed() ** 2 / self.sat.get_radius() * np.sin(angle) ** 2
                T *= self.sat.mass / np.cos(angle)
                self.sat.get('main').on(power=T / self.sat.get('main').thrust_max)

                epsilon = self.reach_geo['epsilon']['radius']
                if 1 - epsilon < self.sat.get_radius() / self.reach_geo['radius'] < 1 + epsilon:
                    epsilon = self.reach_geo['epsilon']['speed']
                    if 1 - epsilon < self.sat.get_speed() / self.reach_geo['speed'] < 1 + epsilon:
                        epsilon = self.reach_geo['epsilon']['angle']
                        if 1 - epsilon < angle/ (np.pi / 2) < 1 + epsilon:
                            ur = normalize(self.sat.x)
                            self.sat.x = ur * self.reach_geo['radius']
                            self.sat.v = np.cross(-ur, self.z) * self.reach_geo['speed']
                            self.sat.get('main').off()
                            print(f"   | ctr: geo reached (forced)     ({self.simulator.time} sec)")
                            self.reach_geo = None
                            self.reach_sync = self.sat.controls['ctr-run-synchronize'] = [((0, {}))]
        # Instruction : Synchroniser la rotation avec la période orbitale
        elif not self.reach_sync is None:
            if self.reach_sync['step'] == 'stop':
                if self.reach_sync['iteration'] == self.reach_sync['n']:
                    self.sat.get(self.reach_sync['thruster']).off()
                    self.reach_sync = {'step': 'wait', 'epsilon': 0.005, 'period': self.get_period()}
                    #print(f"   | ctr: wait to synchronize rotation   ({self.simulator.time} sec)")
                else:
                    self.reach_sync['iteration'] += 1
            if self.reach_sync['step'] == 'wait':
                cos_ang = np.dot(normalize(self.sat.x - self.planet.x), np.cross(normalize(self.sat.ux), self.z))
                if cos_ang > 1 - self.reach_sync['epsilon']:
                    self.reach_sync = self.power_for_rotation(period=self.reach_sync['period'])
                    self.reach_sync['step'], self.reach_sync['iteration'] = 'sync', 0
                    self.sat.get(self.reach_sync['thruster']).on(power=self.reach_sync['power'])
            if self.reach_sync['step'] == 'sync':
                if self.reach_sync['iteration'] == self.reach_sync['n']:
                    self.sat.get(self.reach_sync['thruster']).off()
                    print(f"   | ctr: finish to synchronize rotation   ({self.simulator.time} sec)")
                    self.reach_sync = None
                else:
                    self.reach_sync['iteration'] += 1
        # Instruction : Réaliser un transfert d'Hohmann
        elif not self.do_homhann is None:
            if self.do_homhann['step'] == 'reach_elliptic':
                if self.do_homhann.get('rot'):
                    if self.do_homhann['rot']['n'] == self.do_homhann['iteration']:
                        self.sat.get(self.do_homhann['rot']['thruster']).off()
                if self.do_homhann['n'] == self.do_homhann['iteration']:
                    self.do_homhann['step'] = 'on_elliptic'
                    print(f"   | ctr: elliptical orbit reached   ({self.simulator.time} sec)")
                    self.sat.get(self.do_homhann['thruster']).off()
                else:
                    self.do_homhann['iteration'] += 1
            if self.do_homhann['step'] == 'on_elliptic' and self.simulator.time >= self.do_homhann['stop_at']:
                r = self.do_homhann['radius']
                dv = self.geo_speed(radius=r) - self.sat.get_speed()
                self.do_homhann = self.power_for_speed(speed=dv)
                if self.do_homhann is None:
                    print(f'   | ctr: impossible to reach second GEO   ({self.simulator.time} sec)')
                    return
                else:
                    self.do_homhann['radius'] = r
                    self.sat.get(self.do_homhann['thruster']).on(power=self.do_homhann['power'])
                    self.do_homhann['step'], self.do_homhann['iteration'] = 'reach_geo', 0
            if self.do_homhann['step'] == 'reach_geo':
                if self.do_homhann['iteration'] == self.do_homhann['n']:
                    self.sat.get(self.do_homhann['thruster']).off()

                    # CHEAT :
                    ur = normalize(self.sat.x - self.planet.x)
                    self.sat.x = self.do_homhann['radius'] * ur
                    self.sat.v = self.geo_speed(radius=self.do_homhann['radius']) * np.cross(-ur, self.z)

                    print(f"   | ctr: successful Homhann transfer     ({self.simulator.time} sec)")
                    self.do_homhann = None
                    self.reach_sync = self.sat.controls['ctr-run-synchronize'] = [((0, {}))]
                else:
                    self.do_homhann['iteration'] += 1
