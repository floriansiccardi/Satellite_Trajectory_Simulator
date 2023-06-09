import numpy as np
from random import randint


class Object:

    def __init__(self, mass, name='unamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0)):
        self.mass = mass
        self.simulator = None
        self.scale = 1

        # Position, Vitesse et Accélération :
        self.x, self.v, self.a = np.array(x), np.array(v), np.array(a)
        self.alive = True

        # Identification :
        self.id = randint(0, 99999)
        self.name = name

    def __eq__(self, other):
        return self.id == other.id

    def linkto(self, simulator):
        self.simulator = simulator

    def get_a(self, planets):
        a = np.array([0, 0, 0])
        for pln in planets:
            if pln != self:
                d = self.x - pln.x          # Vecteur direction
                u = -d / np.linalg.norm(d)  # Vecteur direction normalisé (sens opposé)
                a = a + u * 6.67*10**-11 * pln.mass / (np.linalg.norm(d) ** 2)    # a = F / m
        return a
    
    def check_for_collision(self, planets):
        for pln in planets:
            if np.linalg.norm(self.x - pln.x) < pln.radius:
                print(f"   Satellite {self.name} crashed into {pln.name} after {time()-self.simulator.t0} sec alive")
                self.alive = False
                self.x = pln.x + (self.x - pln.x) / np.linalg.norm(self.x - pln.x) * pln.radius
                break

    def step(self, planets):
        self.a = self.get_a(planets=planets)
        self.x, self.v, self.a = self.simulator.integrate(f=self.x, df=self.v, ddf=self.a)
        self.check_for_collision(planets=planets)
