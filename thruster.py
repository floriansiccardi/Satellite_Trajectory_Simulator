import numpy as np
from tools import zero


class Thruster:

    def __init__(self, xr, thrust_max, axe='xp', name='unnamed'):
        self.xr = xr

        self.axe = axe[0]
        if axe[1] == 'p':
            self.side = +1
        elif axe[1] == 'm':
            self.side = -1
        axes = {'x': np.array([1, 0, 0]), 'y': np.array([0, 1, 0]), 'z': np.array([0, 0, 1])}
        self.direction = axes[self.axe] * self.side

        self.power = 0.
        self.thrust_max = thrust_max
        self.thrust = zero()

        self.torque_max = np.dot(self.thrust_max, np.cross(self.xr, self.direction))
        self.torque = zero()

        self.name = name

    def on(self, power=1.): # Par défaut à 100%
        self.power = max(min(power, 1), 0)
        self.thrust = np.dot(self.power * self.thrust_max, self.direction)
        self.torque = np.dot(self.power, self.torque_max)

    def off(self):
        self.power = 0.
        self.thrust = zero()
        self.torque = zero()

