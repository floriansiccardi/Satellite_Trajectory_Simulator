import numpy as np
from random import randint


class Object:

    def __init__(self, mass, x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0), name=''):
        self.simulator = None

        # Position, Vitesse et Accélération :
        self.x, self.v, self.a = np.array(x), np.array(v), np.array(a)

        # Identification :
        self.id = randint(0, 99999)
        self.name = name

    def __eq__(self, other):
        return self.id == other.id

    def linkto(self, simulator):
        self.simulator = simulator

    def step(self):
        self.v, self.a = self.simulator.integrate(f=self.v, df=self.a)
        self.x, self.v = self.simulator.integrate(f=self.x, df=self.v)
