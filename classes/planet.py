import numpy as np
import matplotlib.pyplot as plt
from classes.object import Object

class Planet(Object):

    def __init__(self, radius, mass, name='unnamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0)):
        """
       Initialise un objet de classe Planet.

       :param radius: Rayon de la planète.
       :type radius: float
       :param mass: Masse de la planète.
       :type mass: float
       :param name: Nom de la planète (par défaut 'unnamed').
       :type name: string
       :param x: Coordonnées initiales de la planète (par défaut (0, 0, 0)).
       :type x: 1D-array or tuple   (3 components)
       :param v: Vitesse initiale de la planète (par défaut (0, 0, 0)).
       :type v: 1D-array or tuple   (3 components)
       :param a: Accélération initiale de la planète (par défaut (0, 0, 0)).
       :type a: 1D-array or tuple   (3 components)
       """
        super().__init__(mass=mass, x=x, v=v, a=a, name=name)
        self.radius = radius

    def plot(self, fig=None, ax=None, display=True, N_points=600):
        """
        Trace la représentation en 3D de la planète.

        :param fig: Objet de la figure matplotlib (Si None, création d'une nouvelle).
        :type fig: figure    (from matplotlib)
        :param ax: Objet des axes matplotlib en 3D (Si None, création d'une nouvelle).
        :type ax: axe    (from matplotlib)
        :param display: Indique si le tracé doit être affiché (par défaut True).
        :type display: boolean
        :param N_points: Nombre de points à tracer sur la surface de la planète (par défaut 600).
        :type N_points: int
        :return: Figure et des axes matplotlib mis à jour.
        :rtype: figure, axe    (from matplotlib)
        """
        if fig is None or ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
        # Définition des angles azimutal et polaire
        theta = np.linspace(0, 2 * np.pi, round(np.sqrt(N_points*2)))  # Angle azimutal
        phi = np.linspace(0, np.pi, round(np.sqrt(N_points/2)))  # Angle polaire

        # Calcul des coordonnées des points sur la surface de la planète
        x = self.radius * np.outer(np.cos(theta), np.sin(phi)) + self.x[0]
        y = self.radius * np.outer(np.sin(theta), np.sin(phi)) + self.x[1]
        z = self.radius * np.outer(np.ones(np.size(theta)), np.cos(phi)) + self.x[2]
        # Tracé de la surface de la planète en 3D
        ax.plot_surface(x, y, z, color='b', alpha=0.7)

        if display:
            ax.axis('equal')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            plt.show()
        return fig, ax
