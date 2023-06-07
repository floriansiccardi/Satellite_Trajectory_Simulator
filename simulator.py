from planet import Planet
from satellite import Satellite


class Simulator:

    def __init__(self, dt=1):
        self.dt = dt

        # Entités :
        self.satellites = []
        self.planets = []

    def add(self, obj):
        if type(obj) == Satellite:
            self.satellites.append(obj)
        elif type(obj) == Planet:
            self.planets.append(obj)

    def get(self, name):
        for entities in [self.satellites, self.planets]:
            for ent in entities:
                if ent.name == name:
                    return ent

    def step(self):
        for entities in [self.satellites, self.planets]:
            for ent in entities:
                ent.step()
