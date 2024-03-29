import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.pyplot as plt
from stl import mesh


class STLReader:

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
        axes = figure.add_subplot(111, projection='3d')

        # Plot the mesh
        axes.add_collection3d(Poly3DCollection(self.faces))
        # axes.scatter(self.vertices[:, 0], self.vertices[:, 1], self.vertices[:, 2])
        print(self.vertices)

        # Set plot limits and labels
        axes.set_xlabel('X')
        axes.set_ylabel('Y')
        axes.set_zlabel('Z')

        # # Auto scale to the mesh size
        scale = self.data.points.flatten()
        axes.auto_scale_xyz(scale, scale, scale)

        # Show the plot
        plt.show()


