import numpy as np
from classes.tools import zero


class Thruster:

    def __init__(self, xr, thrust_max, axe='xp', name='unnamed'):
        """
        Initialise un objet de la classe thruster.

        :param xr: (array-like) Vecteur représentant la position du propulseur par rapport au centre de masse de l'objet.
        :param thrust_max: (array-like) Vecteur représentant la valeur maximale de la poussée du propulseur dans
                                        chaque direction.
        :param axe: (str, optional) Axe de direction du propulseur. Peut être 'x', 'y' ou 'z'.
        :param name: (str, optional) Nom du propulseur.
        """
        # Position du propulseur par rapport au centre de masse de l'objet
        self.xr = xr
        # Axe de direction du propulseur
        self.axe = axe[0]
        if axe[1] == 'p':
            self.side = +1 # Sens de la direction du propulseur
        elif axe[1] == 'm':
            self.side = -1
        axes = {'x': np.array([1, 0, 0]), 'y': np.array([0, 1, 0]), 'z': np.array([0, 0, 1])}
        self.direction = axes[self.axe] * self.side # Vecteur de direction du propulseur

        self.power = 0. # Puissance du propulseur
        self.thrust_max = thrust_max # Valeur maximale de la poussée du propulseur dans chaque direction
        self.thrust = zero()  # Vecteur de poussée du propulseur

        self.torque_max = np.dot(self.thrust_max, np.cross(self.xr, self.direction)) # Moment de couple maximal du propulseur
        self.torque = zero() # Moment de couple du propulseur

        self.name = name # Nom du propulseur

    def on(self, power=1.):
        """
        Active le propulseur avec une certaine puissance.

        :param power: (float, optional) Puissance du propulseur, exprimée en fraction de pourcentage (0-1).
                                        Par défaut, la puissance est à 100%.
        """
        self.power = max(min(power, 1), 0)
        self.thrust = np.dot(self.power * self.thrust_max, self.direction)
        self.torque = np.dot(self.power, self.torque_max)

    def off(self):
        """
        Désactive le propulseur en le mettant hors tension.
        """
        # Met la puissance du propulseur à zéro
        self.power = 0.
        
        # Réinitialise les vecteurs de poussée et de couple à zéro
        self.thrust = zero()
        self.torque = zero()
