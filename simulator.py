import matplotlib.pyplot as plt
from planet import Planet
from satellite import Satellite
import tools


class Simulator:

    def __init__(self, dt=1):
        self.dt = dt

        # Entités :
        self.satellites = []
        self.planets = []

    def add(self, obj):
        if type(obj) == Satellite:
            obj.linkto(simulator=self)
            self.satellites.append(obj)
        elif type(obj) == Planet:
            obj.linkto(simulator=self)
            self.planets.append(obj)
        else:
            print(f" > Impossible d'ajouter ce type d'objet à la simulation")

    def get(self, name):
        for entities in [self.satellites, self.planets]:
            for ent in entities:
                if ent.name == name:
                    return ent

    def integrate(self, f, df):
        return tools.euler(f, df, self.dt)

    def show(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for pln in self.planets:
            x, y, z = pln.plot(display=False)
            ax.plot_surface(x, y, z, color='b', alpha=0.7)
        for sat in self.satellites:
            x, y, z = sat.plot(display=False)
            ax.plot_surface(x, y, z, color='b', alpha=1)
        plt.show()



    def step(self):
        for entities in [self.satellites, self.planets]:
            for ent in entities:
                ent.step()
