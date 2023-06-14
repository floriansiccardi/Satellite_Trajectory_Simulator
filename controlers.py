import numpy as np
from tools import normalize


class Controler:

    def __init__(self, sat=None):
        self.G = 6.6743015 * 10 ** -11
        self.mass = 5.9722 * 10 ** 24
        self.radius = 6.371 * 10 ** 6
        self.sat = sat

        # Reach next GEO orbit
        self.reach_geo = False
        self.reach_geo_steps = {}
        self.reach_geo_iteration = 0

        # Synchronize GEO
        self.set_geosync = False
        self.set_geosync_steps = {}
        self.set_geosync_iteration = 0

    def geo_speed(self, radius):
        """
        Retourne la vitesse nécessaire pour maintenir l'orbite GEO au rayon demandé
        :param radius: (float) rayon autour du centre de l'astre (en m)
        :return: (float) vitesse tangentielle (en m/s)
        """
        return np.sqrt(self.G * self.mass / radius)

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

    def get_angle_with_ground(self, args={}):
        uv = normalize(self.sat.v)
        ur = normalize(self.sat.x - self.sat.planet_ref.x)
        return np.arccos(np.dot(uv, ur))

    def update(self, infos=True):
        if self.reach_geo:
            threshold = 0.01
            angle = self.get_angle_with_ground()
            if self.reach_geo_steps:
                if self.reach_geo_iteration == self.reach_geo_steps['niteration']:
                    self.sat.get(self.reach_geo_steps['thruster']).off()
                    self.reach_geo, self.reach_geo_steps, self.reach_geo_iteration = False, {}, 0
                else:
                    self.reach_geo_iteration += 1
            elif np.pi / 2 * (1 - threshold) < angle < np.pi / 2 * (1 + threshold):
                    radius = np.linalg.norm(self.sat.x - self.sat.planet_ref.x)
                    delta_speed = self.geo_speed(radius=radius) - np.linalg.norm(self.sat.v)
                    self.reach_geo_steps = self.power_for_speed(speed=delta_speed, dt=self.sat.simulator.dt,
                                                                     direction=normalize(self.sat.v))
                    if self.reach_geo_steps:
                        self.sat.get(self.reach_geo_steps['thruster']).on(self.reach_geo_steps['power'])
                        if infos:
                            print(f" > Start to reach GEO, {self.reach_geo_steps['niteration']} iteration needed" + ' '*3 + f"({self.sat.simulator.time} sec)")
        if self.set_geosync:
            threshold = 0.02
            angle = self.get_angle_with_ground()
            if np.pi/2*(1-threshold) < angle < np.pi/2*(1+threshold):
                if self.set_geosync_steps:
                    if self.set_geosync_iteration < self.set_geosync_steps['niteration']:
                        self.sat.get(self.set_geosync_steps['thruster']).off()
                        self.set_geosync_steps, self.set_geosync_iteration = {}, 0
                else:
                    radius = np.linalg.norm(self.sat.x - self.sat.planet_ref.x)
                    delta_speed = self.geo_speed(radius=radius) - np.linalg.norm(self.sat.v)
                    self.set_geosync_steps = self.power_for_rotation(speed=delta_speed, dt=self.sat.simulator.dt,
                                                                     direction=normalize(self.sat.v))
                    if self.set_geosync_steps:
                        self.sat.get(self.set_geosync_steps['thruster']).on(self.set_geosync_steps['power'])
                        if infos:
                            print(f" > Start synchronize rotation, {self.set_geosync_steps['niteration']} iteration needed")
