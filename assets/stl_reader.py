import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.pyplot as plt
from stl import mesh


class STL_Reader:

    def __init__(self, path=None):
        self.path, self.data, self.isLoaded = None, None, False
        self.vertices, self.faces = np.array([]), np.array([])
        if not path is None:
            self.open(path)

    def __call__(self, *args, **kwargs):
        print(f" > Informations :\n    fichier : {self.path}\n    points : {len(self.vertices)}")

    def open(self, path):
        try:
            self.data = mesh.Mesh.from_file(path)
            self.path = path
            self.vertices = self.data.vectors.reshape(-1, 3)
            self.faces = self.data.vectors
            self.isLoaded = True
        except FileNotFoundError:
            print(f"\n > Impossible d'ouvrir le fichier STL : {path}")

    def get_GC(self):
        return np.mean(self.vertices, axis=0)

    def show(self):
        # Create a new plot
        figure = plt.figure()
        axes = Axes3D(figure)

        # Plot the mesh
        axes.add_collection3d(Poly3DCollection(self.faces))
        axes.scatter(self.vertices[:, 0], self.vertices[:, 1], self.vertices[:, 2])

        # Set plot limits and labels
        axes.set_xlim3d(np.min(self.vertices[:, 0]), np.max(self.vertices[:, 0]))
        axes.set_ylim3d(np.min(self.vertices[:, 1]), np.max(self.vertices[:, 1]))
        axes.set_zlim3d(np.min(self.vertices[:, 2]), np.max(self.vertices[:, 2]))
        axes.set_xlabel('X')
        axes.set_ylabel('Y')
        axes.set_zlabel('Z')

        # Show the plot
        plt.show()


stl = STL_Reader()
stl.open(path='iss_v2.stl')
print(stl.get_GC())
stl.show()
