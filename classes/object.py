import numpy as np
from random import randint
from tools import normalize, zero


class Object:

    def __init__(self, mass, name='unnamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0)):
        """
        Initialise un objet de la classe object.

        :param mass: (float) Masse de l'objet.
        :param name: (str, optional) Nom de l'objet (par défaut 'unnamed').
        :param x: (tuple, optional) Coordonnées spatiales de l'objet (par défaut (0, 0, 0)).
        :param v: (tuple, optional) Vitesse de l'objet (par défaut (0, 0, 0)).
        :param a: (tuple, optional) Accélération de l'objet (par défaut (0, 0, 0)).
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

        :param other: (object) Autre objet à comparer avec l'objet actuel.
        :return: (bool) True si les objets sont égaux, False sinon.
        """
        return self.id == other.id

    def linkto(self, simulator):
        """
        Lie l'objet actuel à un simulateur spécifié.

        :param simulator: (object) Simulateur auquel l'objet actuel doit être lié.
        """
        self.simulator = simulator

    def get_ag(self, planets):
        """
        Calcule et retourne l'accélération gravitationnelle subie par l'objet en présence des planètes spécifiées.

        :param planets: (list) Liste des objets planètes.
        :return: (1D array, 3 values) Accélération gravitationnelle subie par l'objet.
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
        Vérifie s'il y a une collision entre l'objet satellite et les planètes spécifiées.

        :param planets: (list) Liste des objets planètes.
        """
        for pln in planets:
            # Si la distance entre le satellite et la planète est inférieure au rayon de la planète
            if np.linalg.norm(self.x - pln.x) < pln.radius:
                print(f"   Satellite {self.name} crashed into {pln.name} after {self.simulator.time} sec alive")
                # Marquer le satellite comme détruit
                self.alive = False
                self.x = pln.x + (self.x - pln.x) / np.linalg.norm(self.x - pln.x) * pln.radius
                break



