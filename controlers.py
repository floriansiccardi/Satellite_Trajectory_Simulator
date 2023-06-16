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
        """
        Calcule la période orbitale du satellite.

        :return: (float) la période orbitale (en s^-1)
        """
        # Calcul de la distance entre la position du satellite et la position de référence de la planète
        distance = np.linalg.norm(self.sat.x - self.sat.planet_ref.x)

        # Calcul de la norme (magnitude) de la vitesse du satellite
        vitesse = np.linalg.norm(self.sat.v)

        # Calcul de la période
        periode = 2 * np.pi * (distance / vitesse)

        return periode

    def geo_transfert(self, r1, r2):
        """
        Retourne la vitesse

        :param r1: (float) rayon GEO de l'orbit de départ (en m)
        :param r2: (float) rayon GEO de l'orbit d'arrivée (en m)
        :return: (1D array, 2 values) vitesse de départ pour se placer en elliptique, vitesse d'arrivée (en m/s)
        """
        v = np.array([1 / r1, 1 / r2])

        # Calcul de la différence des vitesses nécessaires pour les orbites elliptiques
        difference_vitesses = v - 1 / (r1 + r2)

        # Calcul de la vitesse nécessaire en utilisant la formule de la vitesse de libération
        vitesse_depart = np.sqrt(np.dot(2 * self.G * self.mass, difference_vitesses))

        return vitesse_depart

    def power_for_speed(self, speed, dt, niteration=1, direction=(1, 0, 0)):
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
        for n in range(niteration, 20 * niteration):  # Essaie en n itérations, sinon essaie avec n+1, ...
            for thruster in self.sat.thrusters:  # Essaie tous les thrusters possibles
                # Calcul de la valeur maximale de poussée du thruster dans la direction souhaitée
                thrust_max = thruster.thrust_max * np.dot(thruster.direction, direction)
                if thrust_max != 0:
                    # Calcul de la puissance nécessaire pour atteindre la vitesse souhaitée
                    power = self.sat.mass * speed / (n * dt * thrust_max)
                    if 0 <= power <= 1.:  # Vérification de la plage de puissance valide (0% à 100%)
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
                    # Calcul de la puissance nécessaire pour effectuer une rotation avec la période souhaitée
                    power = 2*np.pi * self.sat.inertia[axe] / (n * dt * period * thruster.torque_max[axe])
                    if 0 <= power <= 1.:  # Vérification de la plage de puissance valide (0% à 100%)
                        return {'power': power, 'niteration': n, 'thruster_name': thruster.name}

    def power_for_join_GEO(self):
        Fg = self.sat.a

    def get_angle_from_ground(self):
        """
        Calcule l'angle entre la direction de l'axe x du satellite et la direction du sol.

        :return: (float) Angle entre la direction de l'axe x du satellite et la direction du sol (en radians).
        """
        return np.arccos(self.sat.ux[0])

    def update(self, infos=True):
        """
        Met à jour les paramètres et l'état du satellite lors d'une mise à jour de l'orbite.

        :param infos: (bool) Indique si les informations doivent être affichées (par défaut True).
        """
        if not self.reach_geo is None:
            gamma = 10**-6         # Puissance par mètre
            ur, r = normalize(self.sat.x - self.sat.planet_ref.x), self.sat.get_radius()
            theta = np.arccos(np.dot(self.sat.ux, ur))

            # Calcul de la puissance statique
            power_stat = np.linalg.norm(self.sat.ag) * self.sat.mass / (self.sat.get('main').thrust_max * np.cos(theta))
            # Calcul de la puissance dynamique
            power_dyna = gamma * (self.reach_geo - r)
            # Activation du thruster principal avec la puissance combinée
            self.sat.get('main').on(power=power_stat+power_dyna)

            # CHEAT :
            if r >= self.reach_geo:
                prev_r, prev_v = r, self.sat.get_speed()
                # Mise à jour de la position et de la vitesse pour atteindre l'orbite GEO
                self.sat.x = self.reach_geo * ur
                self.sat.v = self.geo_speed(radius=self.reach_geo) * np.cross(-ur, np.array([0, 0, 1]))

                self.sat.get('main').off()
                self.reach_geo = None

                # Calcul des écarts de position et de vitesse par rapport à l'orbite GEO
                delta_r = abs(round(100 * (prev_r - self.sat.get_radius()) / prev_r, 2))
                delta_v = abs(round(100 * (prev_v - self.sat.get_speed()) / prev_v, 2))
                # Affichage des informations
                print(f"   | GEO orbit forced ({delta_r}% for position, {delta_v}% for speed)")
                print(f"     GEO orbit reached at {self.sat.simulator.time} sec")








