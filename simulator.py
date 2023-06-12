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

        self.t0 = None

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

    def count_alive(self):
        count = 0
        for sat in self.satellites:
            count += sat.alive
        return count

    def run(self, time_max=60, iteration_max=10**8, infos=0):
        print(f" > Start simulation ...")
        self.running = True
        self.t0 = time()
        while self.running:
            self.step(infos)
            if infos and self.iteration % infos == 0:
                for sat in self.satellites:
                    if not sat.planet_ref is None:
                        print(f" - Altitude de {sat.name} selon {sat.planet_ref.name} : {round(sat.get_altitude())} m")
                        print(f"   Speed : {round(np.linalg.norm(sat.v))} m/s")

            self.iteration += 1
            if time()-self.t0 >= time_max or self.iteration >= iteration_max or self.count_alive() == 0:
                self.stop()
                return False
        return True

    def step(self, infos=False):
        for sat in self.satellites:
            sat.step(planets=self.planets)
            self.saves[sat.name].append(sat.x)

            # Controls for next step :
            if not sat.controls is None:
                for controler in sat.controls.keys():
                    for step in sat.controls[controler]:  # step = (iteration, value)
                        iteration, value = step[0], step[1]
                        if self.iteration == iteration:
                            if infos:
                                print(f"   | set {controler} to {value}")
                            if '-' in controler:
                                if controler[:8] == 'thruster':
                                    sat.get(controler[9:]).on(power=value)
                            else:
                                setattr(sat, controler, value)

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
                ax.plot(self.saves[sat.name][:, 0], self.saves[sat.name][:, 1], self.saves[sat.name][:, 2],  '-' + sat.color)
        ax.axis('equal')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.show()

    def trajectory(self):
        self.plot(trajectory=True)

    def run_live_simulation(self, time_max=60, iteration_max=10**8, infos=0, trajectory=False):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        print(f" > Start simulation ...")
        self.running = True
        self.t0 = time()
        while self.running:
            self.step(infos=infos)
            if infos and self.iteration % infos == 0:
                for sat in self.satellites:
                    if not sat.planet_ref is None:
                        print(f" - Altitude de {sat.name} selon {sat.planet_ref.name} : {round(sat.get_altitude())} m")
                        print(f"   Speed : {round(np.linalg.norm(sat.v))} m/s")

            self.iteration += 1
            if time() - self.t0 >= time_max or self.iteration >= iteration_max or self.count_alive() == 0:
                self.stop()

            plt.cla()
            ax.axis('equal')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            for pln in self.planets:
                fig, ax = pln.plot(fig=fig, ax=ax, display=False)
            for sat in self.satellites:
                fig, ax = sat.plot(fig=fig, ax=ax, display=False)
                if trajectory:
                    saves_arr = np.array(self.saves[sat.name])
                    ax.plot(saves_arr[:, 0], saves_arr[:, 1], saves_arr[:, 2], '-' + sat.color)
            plt.pause(0.01)
        plt.show()

