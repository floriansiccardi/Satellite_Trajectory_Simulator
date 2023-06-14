import numpy as np
import matplotlib.pyplot as plt
from object import Object
from thruster import Thruster
from controlers import Controler
from tools import rotation_matrix, zero, from_other_base


class Satellite(Object):

    def __init__(self, mass, name='unamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0), size=(1, 1, 1), planet_ref=None):
        super().__init__(mass=mass, x=x, v=v, a=a, name=name)
        self.size = np.array(size)
        self.color = 'g'

        # Positions de référence
        self.ux, self.uy, self.uz = np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])
        self.planet_ref = planet_ref
        self.islanded = False     # False une fois décollé, pour éviter de détecter un crash avant même le décolage
        self.istakingoff = False    # Période courte de transition de landed = True vers False

        # Thruster
        self.thrusters = []                 # Liste des thrusters
        self.thrust = zero()   # Force en N
        self.torque = zero()
        self.inertia = 1/12 * self.mass * np.array([self.size[1]**2 + self.size[2]**2, self.size[0]**2 + self.size[2]**2, self.size[0]**2 + self.size[1]**2])
        self.a_ang, self.v_ang, self.x_ang = zero(), zero(), zero()

        # Controlers :
        self.controls = {}          # Manuals controls
        self.controler = None       # Automatic controler

    def set_scale(self, scale):
        self.scale = scale
        self.size = np.dot(scale, self.size)

    def set_planet_ref(self, planet_ref):
        self.planet_ref = planet_ref

    def add(self, obj):
        if type(obj) == Thruster:
            self.thrusters.append(obj)
        elif type(obj) == Controler:
            self.controler = obj
        else:
            print(f" > Impossible d'ajouter ce type d'objet à la simulation")

    def get(self, name):
        for thruster in self.thrusters:
            if thruster.name == name:
                return thruster

    def get_altitude(self):
        if self.planet_ref is None:
            print(f" /!\\ Aucune planète référence n'a été donné. L'altitude retournée est donc nulle")
            return 0
        return np.linalg.norm(self.x - self.planet_ref.x) - self.planet_ref.radius

    def get_axes(self, dalpha=(0, 0, 0)):
        for axe, delta in enumerate(dalpha):
            if delta != 0:
                rot = rotation_matrix(angle=delta, axe=axe)
                # Note : tourner x autour de x n'a aucun intêret, possibilité d'optimiser ça
                self.ux, self.uy, self.uz = np.dot(rot, self.ux), np.dot(rot, self.uy), np.dot(rot, self.uz)
        return self.ux, self.uy, self.uz

    def get_thrust(self):
        self.thrust, self.torque = zero(), zero()
        # Update thrusters :
        for thruster in self.thrusters:
            self.thrust = self.thrust + thruster.thrust
            self.torque = self.torque + thruster.torque
        self.thrust = from_other_base(point=self.thrust, base=[self.ux, self.uy, self.uz])
        self.torque = from_other_base(point=self.torque, base=[self.ux, self.uy, self.uz])

        return self.thrust, self.torque

    def step(self, planets, infos=0):
        if self.alive and (not self.islanded or self.istakingoff):
            F, C = self.get_thrust()
            # Force :
            self.a = self.get_a(planets=planets) + F / self.mass
            self.x, self.v, self.a = self.simulator.integrate(f=self.x, df=self.v, ddf=self.a)
            # Couple :
            self.a_ang = C / self.inertia
            self.x_ang, self.v_ang, self.a_ang = self.simulator.integrate(f=zero(), df=self.v_ang, ddf=self.a_ang)
            self.get_axes(dalpha=self.x_ang)
            if not (self.islanded or self.istakingoff):
                self.check_for_collision(planets=planets)
        self.update_controls(infos=infos)

    def update_controls(self, infos=0):
        for controler in self.controls.keys():
            for step in self.controls[controler]:  # step = (time, value)
                time, value = step[0], step[1]
                if self.simulator.time >= time:
                    if infos:
                        print(f"   | set {controler} to {value}" + ' '*3 + f"({self.simulator.time} sec)")
                    if '-' in controler:
                        if controler[:8] == 'thruster':
                            self.get(controler[9:]).on(power=value)
                        if controler[:3] == 'ctr':
                            if controler[4:7] == 'run':
                                getattr(self.controler, controler[8:])(value)   # Run function with args
                            else:
                                setattr(self.controler, controler[4:], value)
                    else:
                        setattr(self, controler, value)
                    self.controls[controler].remove(step)

    def plot(self, fig=None, ax=None, display=True):
        if fig is None or ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')

        # Coordonnées des sommets du cube
        vertices = np.zeros((8, 3))
        vertices[1], vertices[2] = self.size[0] * self.ux, self.size[0] * self.ux + self.size[1] * self.uy
        vertices[3] = self.size[1] * self.uy
        vertices[4:] = vertices[:4] + self.size[2] * self.uz
        vertices += self.x - np.dot(np.array(self.size), np.array([self.ux, self.uy, self.uz])) / 2

        # Indices des faces du cube
        faces = np.array([[0, 1, 2, 3], [4, 5, 6, 7],  [0, 1, 5, 4],
                          [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])

        # Tracer les faces du cube
        for face in faces:
            x, y, z = vertices[face, 0], vertices[face, 1], vertices[face, 2]
            x[2::], y[2::], z[2::] = x[:1:-1], y[:1:-1], z[:1:-1]
            ax.plot_surface(x.reshape((2, 2)), y.reshape((2, 2)), z.reshape((2, 2)), facecolors=self.color)

        if display:
            ax.axis('equal')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            plt.show()
        return fig, ax
