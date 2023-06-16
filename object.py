import numpy as np
from random import randint
from time import time
from tools import normalize, zero


class Object:

    def __init__(self, mass, name='unnamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0)):
        self.mass = mass
        self.simulator = None
        self.scale = 1

        # Position, Vitesse et Accélération :
        self.x, self.v, self.ag = np.array(x), np.array(v), np.array(a)
        self.alive = True

        # Identification :
        self.id = randint(0, 99999)
        self.name = name

    def __eq__(self, other):
        return self.id == other.id

    def linkto(self, simulator):
        self.simulator = simulator

    def get_ag(self, planets):
        self.ag = zero()
        for pln in planets:
            if pln != self:
                d = self.x - pln.x          # Vecteur direction
                u = -normalize(d)  # Vecteur direction normalisé (sens opposé)
                self.ag = self.ag + u * 6.67*10**-11 * pln.mass / (np.linalg.norm(d) ** 2)    # a = F / m
        return self.ag
    
    def check_for_collision(self, planets):
        for pln in planets:
            if np.linalg.norm(self.x - pln.x) < pln.radius:
                print(f"   Satellite {self.name} crashed into {pln.name} after {time()-self.simulator.t0} sec alive")
                self.alive = False
                self.x = pln.x + (self.x - pln.x) / np.linalg.norm(self.x - pln.x) * pln.radius
                break


