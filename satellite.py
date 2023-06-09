import numpy as np
import matplotlib.pyplot as plt
from object import Object


class Satellite(Object):

    def __init__(self, mass, name='unamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0), size=np.array([1, 1, 1])):
        super().__init__(mass=mass, x=x, v=v, a=a, name=name)
        self.size = size
        self.color = 'r'

    def set_scale(self, scale):
        self.scale = scale
        self.size = np.dot(scale, self.size)

    def plot(self, fig=None, ax=None, display=True):
        if fig is None or ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')

        # Coordonnées des sommets du cube
        vertices = np.array([[-self.size[0] / 2, -self.size[1] / 2, -self.size[2] / 2],  # V0
                             [ self.size[0] / 2, -self.size[1] / 2, -self.size[2] / 2],  # V1
                             [ self.size[0] / 2,  self.size[1] / 2, -self.size[2] / 2],  # V2
                             [-self.size[0] / 2,  self.size[1] / 2, -self.size[2] / 2],  # V3
                             [-self.size[0] / 2, -self.size[1] / 2,  self.size[2] / 2],  # V4
                             [ self.size[0] / 2, -self.size[1] / 2,  self.size[2] / 2],  # V5
                             [ self.size[0] / 2,  self.size[1] / 2,  self.size[2] / 2],  # V6
                             [-self.size[0] / 2,  self.size[1] / 2,  self.size[2] / 2]]) # V7
        vertices += self.x

        # Indices des faces du cube
        faces = np.array([[0, 1, 2, 3], [4, 5, 6, 7],  [0, 1, 5, 4],
                          [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])

        # Tracer les faces du cube
        for face in faces:
            x, y, z = vertices[face, 0], vertices[face, 1], vertices[face, 2]
            x[2::], y[2::], z[2::] = x[:1:-1], y[:1:-1], z[:1:-1]
            ax.plot_surface(x.reshape((2, 2)), y.reshape((2, 2)), z.reshape((2, 2)), facecolors=self.color)

        if display:
            ax.axis('equal')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            plt.show()
        return fig, ax
