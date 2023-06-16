import numpy as np
from tools import normalize, sign


class Controler:

    def __init__(self, sat=None):
        self.G = 6.6743015 * 10 ** -11
        self.mass = 5.9722 * 10 ** 24
        self.radius = 6.371 * 10 ** 6
        self.sat = sat

        self.reach_geo = None

    def geo_speed(self, radius):
        """
        Retourne la vitesse nécessaire pour maintenir l'orbite GEO au rayon demandé
        :param radius: (float) rayon autour du centre de l'astre (en m)
        :return: (float) vitesse tangentielle (en m/s)
        """
        return np.sqrt(self.G * self.mass / radius)

    def get_period(self):
        return 2*np.pi * np.linalg.norm(self.sat.x - self.sat.planet_ref.x) / np.linalg.norm(self.sat.v)

    def geo_transfert(self, r1, r2):
        """
        Retourne la vitesse
        :param r1: (float) rayon GEO de l'orbit de départ (en m)
        :param r2: (float) rayon GEO de l'orbit d'arrivée (en m)
        :return: (1D array, 2 values) vitesse de départ pour se placer en eliptique, vitesse d'arrivée (en m/s)
        """
        v = np.array([1 / r1, 1 / r2])
        return np.sqrt(np.dot(2 * self.G * self.mass, v - 1 / (r1 + r2)))

    def power_for_speed(self, speed, dt, niteration=1, direction=(1, 0, 0)):
        """
        Retourne la puissance (de 0% à 100%) à appliquer au thruster précisé en sortie, durant niteration de dt sec,
        afin d'augmenter sa vitesse de speed dans la direction souhaité
        :param speed: (float) Écart de vitesse à ajouter (speed = v_fin - v_init)
        :param dt: (float) Pas de temps discrétisé constant durant la mise en puissance des thruster (en sec)
        :param niteration: (int) Nombre d'iration souhaite. Attention: Celui-ci peut finalement augmenter, si le nombre
                                 d'itération souhaité n'est pas suffisant
        :param direction: (1D array, 3 values) Vecteur directeur normalisé de la direction de la vitesse souhaité
        :return: (dict) {'power': (float) Puissance de 0% à 100% du thruster,
                         'niteration': Nombre d'itération nécessaire à la rotation,
                         'thruster_name': Nom du thruster à activer.
        """
        for n in range(niteration, 20 * niteration):  # Essaie en n itérations, sinon essaie avec n+1, ...
            for thruster in self.sat.thrusters:  # Essaie tous les thrusters possibles
                thrust_max = thruster.thrust_max * np.dot(thruster.direction, direction)
                if thrust_max != 0:
                    power = self.sat.mass * speed / (n * dt * thrust_max)
                    if 0 <= power <= 1.:  # Power de 0% à 100% (min et max)
                        return {'power': power, 'niteration': n, 'thruster': thruster.name}

    def power_for_rotation(self, period, dt, niteration=1, axe=2):
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
        for n in range(niteration, 10 * niteration):  # Essaie en n itérations, sinon essaie avec n+1, ...
            for thruster in self.sat.thrusters:     # Essaie tous les thrusters possibles
                if thruster.torque_max[axe] != 0:
                    power = 2*np.pi * self.sat.inertia[axe] / (n * dt * period * thruster.torque_max[axe])
                    if 0 <= power <= 1.:            # Power de 0% à 100% (min et max)
                        return {'power': power, 'niteration': n, 'thruster_name': thruster.name}

    def power_for_join_GEO(self):
        Fg = self.sat.a

    def get_angle_with_ground(self, args={}):
        uv = normalize(self.sat.v)
        ur = normalize(self.sat.x - self.sat.planet_ref.x)
        return np.arccos(np.dot(uv, ur))

    def get_angle_from_ground(self):
        return np.arccos(self.sat.ux[0])

    def update(self, infos=True):
        if self.reach_geo:
            Fg, theta = np.linalg.norm(self.sat.ag) * self.sat.mass, self.get_angle_from_ground()
            v, r = self.sat.get_speed(), self.sat.get_radius()
            denom = np.cos(theta) * self.sat.get('main').thrust_max
            if denom != 0:
                self.sat.get('main').on((Fg - self.sat.mass * v**2 / r * np.sin(theta)) / denom)
                print(f" | set main power on {self.sat.get('main').power}")







