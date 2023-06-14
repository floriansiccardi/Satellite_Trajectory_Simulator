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
        self.saves_u = {}

        self.t0 = None
        self.time = 0

        self.controls = {}

    def add(self, obj):
        if type(obj) == Satellite:
            obj.linkto(simulator=self)
            self.satellites.append(obj)
            self.saves[obj.name] = [obj.x]
            self.saves_u[obj.name] = [obj.ux, obj.uy, obj.uz]
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

    def run(self, duration_max=60, time_max=10**6, infos=0):
        print(f" > Start simulation ...")
        self.running = True
        self.t0 = time()
        if infos < 1:
            infos = round(infos * time_max)
        next_info = 0
        while self.running:
            self.step(infos)
            if infos and self.time >= next_info:
                next_info += infos
                for sat in self.satellites:
                    if not sat.planet_ref is None:
                        print(f"\n - Altitude de {sat.name} selon {sat.planet_ref.name} : {round(sat.get_altitude())} m")
                        print(f"   Speed : {round(np.linalg.norm(sat.v))} m/s" + ' '*30 + f"({self.time} sec)")

            self.iteration += 1
            if time()-self.t0 >= duration_max or self.time >= time_max or self.count_alive() == 0:
                self.stop()
                return False
        return True

    def step(self, infos=False):
        for sat in self.satellites:
            sat.step(planets=self.planets, infos=infos)
            self.saves[sat.name].append(sat.x)
            self.saves_u[sat.name].append([sat.ux, sat.uy, sat.uz])
        self.time += self.dt

        # Manuals Controls for next step :
        for ctrl in self.controls.keys():
            for step in self.controls[ctrl]:  # step = (time, value)
                time, value = step[0], step[1]
                if self.time >= time:
                    if infos:
                        print(f"   | set {ctrl} to {value}" + ' '*3 + f"({self.time} sec)")
                        setattr(sat, ctrl, value)
                    self.controls[ctrl].remove(step)
        # Automatic controls for next step :
        for sat in self.satellites:
            if not sat.controler is None:
                sat.controler.update()

    def stop(self):
        self.running = False
        print(f"   Simulation ended after {self.iteration} iterations and {round(time() - self.t0, 2)} sec")
        print(f"   Real elapsed time : {timedelta(seconds=self.iteration * self.dt)}")
        for key in self.saves.keys():
            self.saves[key] = np.array(self.saves[key])

    def plot(self, trajectory=True):
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

    def animation(self, trajectory=True, step=1):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for i in range(0, self.iteration, step):
            plt.cla()
            ax.axis('equal')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            for pln in self.planets:
                fig, ax = pln.plot(fig=fig, ax=ax, display=False)
            for sat in self.satellites:
                sat.x = self.saves[sat.name][i]
                sat.ux, sat.uy, sat.uz = self.saves_u[sat.name][i]
                fig, ax = sat.plot(fig=fig, ax=ax, display=False)
                if trajectory:
                    traj = self.saves[sat.name][:i]
                    ax.plot(traj[:, 0], traj[:, 1], traj[:, 2], '-' + sat.color)
            plt.pause(0.01)
        plt.show()


