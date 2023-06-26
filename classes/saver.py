import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Saver:

    def __init__(self):
        self.df = pd.DataFrame(columns=['name', 'time', 'r', 'x1', 'x2', 'x3', 'v', 'dt', 'orientation', 'power'])
        # TITRE : Évolution xxxx en fonction yyyy
        self.title = {'time': 'du Temps', 'r': 'du Rayon', 'v': 'de la Vitesse', 'dt': 'du Pas de temps',
                      'orientation': 'de l\'Orientation', 'power': 'des Puissances'}
        self.units = {'time': 'sec', 'r': 'm', 'v': 'm/s', 'dt': 'sec', 'orientation': 'rad', 'power': '%'}

    def __call__(self, *args, **kwargs):
        print(self.df)

    def __getitem__(self, sat):
        if sat in self.df['name'].unique():
            return self.df[self.df['name'] == sat]

    def save(self, sat):
        self.df.loc[len(self.df.index)] = [sat.name, sat.simulator.time, sat.get_radius(), sat.x[0], sat.x[1], sat.x[2],
                                           sat.get_speed(), sat.simulator.dt, sat.x_ang[2],
                                           {thruster.name: sat.get(thruster.name).power for thruster in sat.thrusters}]

    def plot(self, sat, y, x='time', scaled=True):
        dx, dy = self.__getitem__(sat)[x], self.__getitem__(sat)[y]
        if type(dy[0]) == dict:
            keys = dy[0].keys()
            for key in keys:
                save = []
                for row in dy:
                    save.append(row[key])
                m = max(save)
                if scaled and m != 0 and m != 1:
                    save = [value / m for value in save]
                    plt.plot(dx, save, label=key + f'   (x{round(1/m)})')
                else:
                    plt.plot(dx, save, label=key)
            plt.legend()
        else:
            plt.plot(dx, dy)
        plt.title(f"Évolution {self.title[y]} ({self.units[y]}) en fonction {self.title[x]} ({self.units[x]})")
        plt.xlabel(f"{self.title[x].split(' ')[-1]} ({self.units[x]})")
        plt.ylabel(f"{self.title[y].split(' ')[-1]} ({self.units[y]})")
        plt.show()
