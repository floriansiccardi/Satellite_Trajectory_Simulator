import matplotlib.pyplot as plt
import numpy as np
from planet import Planet
from satellite import Satellite
import tools
from time import time
from datetime import timedelta


class Simulator:

    def __init__(self, dt=20):
        self.dt = dt
        self.running = False
        self.iteration = 0

        # Entités :
        self.satellites = []
        self.planets = []
        self.saves = {}

    def add(self, obj):
        if type(obj) == Satellite:
            obj.linkto(simulator=self)
            self.satellites.append(obj)
            self.saves[obj.name] = [obj.x]
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

    def integrate(self, f, df, ddf):
        return tools.euler(f, df, ddf, self.dt)

    def run(self, time_max=60, iteration_max=10**8):
        print(f" > Start simulation ...")
        self.running = True
        t0 = time()
        while self.running:
            self.step()
            self.iteration += 1
            if time()-t0 >= time_max or self.iteration >= iteration_max:
                print(f"   Simulation ended after {self.iteration} iterations and {round(time()-t0,2)} sec")
                print(f"   Real elapsed time : {timedelta(seconds=self.iteration * self.dt)}")
                self.stop()

    def step(self):
        for sat in self.satellites:
            sat.step(planets=self.planets)
            self.saves[sat.name].append(list(sat.x))

        def stop(self):
        self.running = False
        print(f"   Simulation ended after {self.iteration} iterations and {round(time() - self.t0, 2)} sec")
        print(f"   Real elapsed time : {timedelta(seconds=self.iteration * self.dt)}")
        for key in self.saves.keys():
            self.saves[key] = np.array(self.saves[key])

    def plot(self, trajectory=False):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for pln in self.planets:
            fig, ax = pln.plot(fig=fig, ax=ax, display=False)
        for sat in self.satellites:
            fig, ax = sat.plot(fig=fig, ax=ax, display=False)
            if trajectory:
                ax.plot(self.saves[sat.name][:, 0], self.saves[sat.name][:, 1], self.saves[sat.name][:, 2], '-r')
        ax.axis('equal')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.show()

    def trajectory(self):
        self.plot(trajectory=True)

