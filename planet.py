import numpy as np
import matplotlib.pyplot as plt
from object import Object


class Planet(Object):

    def __init__(self, radius, mass, x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0), name=''):
        super().__init__(mass=mass, x=x, v=v, a=a, name=name)
        self.radius = radius
        self.mass = mass

    def plot(self, display=True, N_points=200):
        theta = np.linspace(0, 2 * np.pi, round(np.sqrt(N_points*2)))  # Angle azimutal
        phi = np.linspace(0, np.pi, round(np.sqrt(N_points/2)))  # Angle polaire

        x = self.radius * np.outer(np.cos(theta), np.sin(phi)) + self.x[0]
        y = self.radius * np.outer(np.sin(theta), np.sin(phi)) + self.x[1]
        z = self.radius * np.outer(np.ones(np.size(theta)), np.cos(phi)) + self.x[2]

        if display:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.plot_surface(x, y, z, color='b', alpha=0.7)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            plt.show()
        return x, y, z

