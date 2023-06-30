import numpy as np
from random import randint
from classes.tools import normalize, zero


class Object:

    def __init__(self, mass, name='unnamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0)):
        """
        Initialise un objet de la classe object.
        Un objet est définit par une position, une vitesse et une accélération, ainsi qu'une masse et un nom et ID.
        Il peut être relié à un simulateur, et peut être considéré comme en vie ou mort.

        :param mass: Masse de l'objet.
        :type mass: float
        :param name: Nom de l'objet (par défaut 'unnamed').
        :type name: str
        :param x: Coordonnées spatiales de l'objet (par défaut (0, 0, 0)).
        :type x: 1D-array or tuple   (3 components)
        :param v: Vitesse de l'objet (par défaut (0, 0, 0)).
        :type v: 1D-array or tuple   (3 components)
        :param a: Accélération de l'objet (par défaut (0, 0, 0)).
        :type a: 1D-array or tuple   (3 components)
        """
        self.mass = mass
        self.simulator = None
        self.scale = 1

        # Position, Vitesse et Accélération :
        self.x, self.v, self.ag = np.array(x), np.array(v), np.array(a)
        self.alive = True

        # Identification :
        self.id = randint(0, 99999)
        self.name = name

    def __eq__(self, other):
        """
        Vérifie si deux objets sont égaux en comparant leurs identifiants.

        :param other: Autre objet à comparer avec l'objet actuel.
        :type other: Object (class)
        :return: True si les objets sont égaux, False sinon.
        :rtype: boolean
        """
        return self.id == other.id

    def linkto(self, simulator):
        """
        Lie l'objet actuel à un simulateur existant.

        :param simulator: Simulateur auquel l'objet actuel doit être lié.
        :type param: Simulator (class)
        """
        self.simulator = simulator

    def get_ag(self, planets):
        """
        Calcule et retourne l'accélération gravitationnelle subie par l'objet en présence des planètes spécifiées.

        :param planets: Liste des objets planètes.
        :type planets: list[Planet (class)]
        :return: Accélération gravitationnelle subie par l'objet.
        :rtype: 1D-array   (3 components)
        """
        # Initialisation de l'accélération gravitationnelle à zéro
        self.ag = zero()
        for pln in planets:
            if pln != self:
                # Vecteur direction entre l'objet actuel et la planète
                d = self.x - pln.x
                # Vecteur direction normalisé (sens opposé)
                u = -normalize(d)
                # Calcul de l'accélération (a = F / m)
                self.ag = self.ag + u * 6.67*10**-11 * pln.mass / (np.linalg.norm(d) ** 2)
        return self.ag
    
    def check_for_collision(self, planets):
        """
        Vérifie s'il y a une collision entre l'objet satellite et les planètes spécifiées, et tue les entitées.

        :param planets: Liste des objets planètes.
        :type planets: list[Planet (class)]
        """
        for pln in planets:
            # Si la distance entre le satellite et la planète est inférieure au rayon de la planète
            if np.linalg.norm(self.x - pln.x) < pln.radius:
                print(f"   Satellite {self.name} crashed into {pln.name} after {self.simulator.time} sec alive")
                # Marquer le satellite comme détruit
                self.alive = False
                self.x = pln.x + (self.x - pln.x) / np.linalg.norm(self.x - pln.x) * pln.radius
                break



