import numpy as np
import matplotlib.pyplot as plt
from object import Object


class Satellite(Object):

    def __init__(self, mass, x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0), name=''):
        super().__init__(mass=mass, x=x, v=v, a=a, name=name)
        pass

    def plot(self, display=True):
        Lx, Ly, Lz = 2, 1, 1

        x = np.outer(np.array([self.x[0]-Lx/2, self.x[0]+Lx/2]), np.ones(4)).T
        x = np.concatenate((x, np.array([x[0, :]])))
        y = np.outer(np.array([self.x[1]-Ly/2, self.x[1]+Ly/2]), np.ones(2))
        y = np.concatenate((y, np.flip(y, axis=0), np.array([y[0, :]])))
        z = np.reshape(np.repeat(np.array([self.x[2]-Lz/2, self.x[2]+Lz/2]), 4), (4, 2))
        z = np.concatenate((z, np.array([z[0, :]])))

        if display:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.plot_surface(x, y, z, color='b', alpha=0.7)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            plt.show()
        return x, y, z