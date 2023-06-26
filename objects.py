import numpy as np
import matplotlib.pyplot as plt
from random import randint
from time import time
from tools import normalize, zero, rotation_matrix, from_other_base
from thruster import Thruster
from controlers import Controler


class Object:

    def __init__(self, mass, name='unnamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0)):
        """
        Initialise un objet de la classe object.

        :param mass: (float) Masse de l'objet.
        :param name: (str, optional) Nom de l'objet (par défaut 'unnamed').
        :param x: (tuple, optional) Coordonnées spatiales de l'objet (par défaut (0, 0, 0)).
        :param v: (tuple, optional) Vitesse de l'objet (par défaut (0, 0, 0)).
        :param a: (tuple, optional) Accélération de l'objet (par défaut (0, 0, 0)).
        """
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
        """
        Vérifie si deux objets sont égaux en comparant leurs identifiants.

        :param other: (object) Autre objet à comparer avec l'objet actuel.
        :return: (bool) True si les objets sont égaux, False sinon.
        """
        return self.id == other.id

    def linkto(self, simulator):
        """
        Lie l'objet actuel à un simulateur spécifié.

        :param simulator: (object) Simulateur auquel l'objet actuel doit être lié.
        """
        self.simulator = simulator

    def get_ag(self, planets):
        """
        Calcule et retourne l'accélération gravitationnelle subie par l'objet en présence des planètes spécifiées.

        :param planets: (list) Liste des objets planètes.
        :return: (1D array, 3 values) Accélération gravitationnelle subie par l'objet.
        """
        # Initialisation de l'accélération gravitationnelle à zéro
        self.ag = zero()
        for pln in planets:
            if pln != self:
                # Vecteur direction entre l'objet actuel et la planète
                d = self.x - pln.x
                # Vecteur direction normalisé (sens opposé)
                u = -normalize(d)
                # Calcul de l'accélération (a = F / m)
                self.ag = self.ag + u * 6.67*10**-11 * pln.mass / (np.linalg.norm(d) ** 2)
        return self.ag
    
    def check_for_collision(self, planets):
        """
        Vérifie s'il y a une collision entre l'objet satellite et les planètes spécifiées.

        :param planets: (list) Liste des objets planètes.
        """
        for pln in planets:
            # Si la distance entre le satellite et la planète est inférieure au rayon de la planète
            if np.linalg.norm(self.x - pln.x) < pln.radius:
                print(f"   Satellite {self.name} crashed into {pln.name} after {self.simulator.time} sec alive")
                # Marquer le satellite comme détruit
                self.alive = False
                self.x = pln.x + (self.x - pln.x) / np.linalg.norm(self.x - pln.x) * pln.radius
                break


class Planet(Object):

    def __init__(self, radius, mass, name='unnamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0)):
        """
       Initialise un objet de classe Planet.

       :param radius: (float) Rayon de la planète.
       :param mass: (float) Masse de la planète.
       :param name: (str, optional) Nom de la planète (par défaut 'unnamed').
       :param x: (tuple, optional) Coordonnées initiales de la planète (par défaut (0, 0, 0)).
       :param v: (tuple, optional) Vitesse initiale de la planète (par défaut (0, 0, 0)).
       :param a: (tuple, optional) Accélération initiale de la planète (par défaut (0, 0, 0)).
       """
        super().__init__(mass=mass, x=x, v=v, a=a, name=name)
        self.radius = radius

    def plot(self, fig=None, ax=None, display=True, N_points=600):
        """
        Trace la représentation en 3D de la planète.

        :param fig: (Figure, optional) Objet de la figure matplotlib (par défaut None).
        :param ax: (Axes3D, optional) Objet des axes matplotlib en 3D (par défaut None).
        :param display: (bool, optional) Indique si le tracé doit être affiché (par défaut True).
        :param N_points: (int, optional) Nombre de points à tracer sur la surface de la planète (par défaut 600).
        :return: (Figure, Axes3D) Objet de la figure et des axes matplotlib.
        """
        if fig is None or ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
        # Définition des angles azimutal et polaire
        theta = np.linspace(0, 2 * np.pi, round(np.sqrt(N_points*2)))  # Angle azimutal
        phi = np.linspace(0, np.pi, round(np.sqrt(N_points/2)))  # Angle polaire

        # Calcul des coordonnées des points sur la surface de la planète
        x = self.radius * np.outer(np.cos(theta), np.sin(phi)) + self.x[0]
        y = self.radius * np.outer(np.sin(theta), np.sin(phi)) + self.x[1]
        z = self.radius * np.outer(np.ones(np.size(theta)), np.cos(phi)) + self.x[2]
        # Tracé de la surface de la planète en 3D
        ax.plot_surface(x, y, z, color='b', alpha=0.7)

        if display:
            ax.axis('equal')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            plt.show()
        return fig, ax


class Satellite(Object):

    def __init__(self, mass, name='unnamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0), size=(1, 1, 1), planet_ref=None):
        """
        Initialise un objet de la classe satellite.

        :param mass: (float) Masse du satellite.
        :param name: (str, optional) Nom du satellite (par défaut 'unnamed').
        :param x: (tuple, optional) Coordonnées spatiales du satellite (par défaut (0, 0, 0)).
        :param v: (tuple, optional) Vitesse du satellite (par défaut (0, 0, 0)).
        :param a: (tuple, optional) Accélération du satellite (par défaut (0, 0, 0)).
        :param size: (tuple, optional) Taille du satellite (par défaut (1, 1, 1)).
        :param planet_ref: (Planet, optional) Référence à la planète associée au satellite (par défaut None).
        """
        super().__init__(mass=mass, x=x, v=v, a=a, name=name)
        self.size = np.array(size)
        self.color = 'g'

        self.radius, self.speed = None, None        # Évite de calculer 2 fois le rayon/vitesse dans une même itération

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
        self.controler = Controler()       # Automatic controler
        self.controler.load(sat=self)

    def set_scale(self, scale):
        """
        Définit l'échelle du satellite.

        :param scale: (float) L'échelle.
        """
        self.scale = scale
        self.size = np.dot(scale, self.size)

    def set_planet_ref(self, planet_ref):
        """
        Définit la référence planétaire pour le satellite.

        :param planet_ref: (Planet) Planète de référence pour le satellite.
        """
        self.planet_ref = planet_ref

    def add(self, obj):
        """
        Ajoute un objet au satellite.

        :param obj: (Object) Objet à ajouter.
        """
        if type(obj) == Thruster: # Si l'objet est de type Thruster
            # Ajoute le thruster à la liste des thrusters du satellite
            self.thrusters.append(obj)
        elif type(obj) == Controler: # Si l'objet est de type Controler
            # Définit le controleur pour le satellite
            self.controler = obj
            self.controler.load(sat=self)
        else:
            print(f" > Impossible d'ajouter ce type d'objet à la simulation")

    def get(self, name):
        """
        Récupère un thruster du satellite par son nom.

        :param name: (str) Nom du thruster à récupérer.
        :return: (Thruster) Le thruster correspondant au nom spécifié, None s'il n'est pas trouvé.
        """
        # Parcours tous les thrusters du satellite
        for thruster in self.thrusters:
            if thruster.name == name: # Si le nom du thruster correspond au nom spécifié
                # Retourne le thruster correspondant
                return thruster
        return None  # Si aucun thruster n'est trouvé avec le nom spécifié, retourne None

    def get_altitude(self):
        """
        Calcule et retourne l'altitude du satellite par rapport à sa planète de référence.

        :return: (float) L'altitude du satellite en mètres.
        """
        # Vérifie qu'une planète de référence soit bien spécifiée
        if self.planet_ref is None:
            print(f" /!\\ Aucune planète référence n'a été donné. L'altitude retournée est donc nulle")
            return 0 # Si aucune planète de référence, retourner une altitude de 0
        return np.linalg.norm(self.x - self.planet_ref.x) - self.planet_ref.radius

    def get_axes(self, dalpha=(0, 0, 0)):
        """
        Calcule et retourne les vecteurs de base des axes du satellite après une rotation.

        :param dalpha: (tuple) Les angles de rotation autour de chaque axe (en radians).
        :return: (tuple) Les vecteurs de base des axes du satellite après la rotation.
        """
        for axe, delta in enumerate(dalpha):
            # Vérifie que l'angle de rotation autour de l'axe soit non nul
            if delta != 0:
                # Calcule de la matrice de rotation correspondante
                rot = rotation_matrix(angle=delta, axe=axe)
                # Note : tourner x autour de x n'a aucun intêret, possibilité d'optimiser ça
                # Applique la rotation aux vecteurs de base ux, uy, uz du satellite
                self.ux, self.uy, self.uz = np.dot(rot, self.ux), np.dot(rot, self.uy), np.dot(rot, self.uz)

        return self.ux, self.uy, self.uz

    def get_thrust(self):
        """
        Calcule et retourne la force totale et le couple total générés par les thrusters du satellite.

        :return: (tuple) Force totale et couple total générés par les thrusters du satellite.
        """
        # Initialisation des forces et du couple à zéro
        self.thrust, self.torque = zero(), zero()

        # Mise à jour des thrusters :
        for thruster in self.thrusters:
            # Accumulation des forces des thrusters
            self.thrust = self.thrust + thruster.thrust
            # Accumulation des couples des thrusters
            self.torque = self.torque + thruster.torque
        # Conversion des forces et du couple dans la base du satellite
        self.thrust = from_other_base(point=self.thrust, base=[self.ux, self.uy, self.uz])
        self.torque = from_other_base(point=self.torque, base=[self.ux, self.uy, self.uz])

        # Renvoie la force totale et le couple total
        return self.thrust, self.torque

    def get_radius(self):
        """
        Calcule et retourne le rayon entre le satellite et à sa planète de référence.

        :return: (float) Rayon entre le satellite et à sa planète de référence.
        """
        # Vérifie si une planète de référence est définie
        if not self.planet_ref is None:
            if self.radius is None:
                # Calcule la distance entre le satellite et sa planète de référence
                self.radius = np.linalg.norm(self.x - self.planet_ref.x)
                return self.radius
            else:
                return self.radius

    def get_speed(self):
        """
        Calcule et retourne la vitesse du satellite.

        :return: (float) Vitesse du satellite.
        """
        if self.speed is None:
            # Retourne la norme du vecteur vitesse du satellite
            self.speed = np.linalg.norm(self.v)
            return self.speed
        else:
            return self.speed

    def step(self, planets, infos=0):
        """
        Effectue un pas de simulation pour le satellite.

        :param planets: (list) Liste des planètes présentes dans la simulation.
        :param infos: (int) Niveau d'informations à afficher.
        """
        if self.alive and (not self.islanded or self.istakingoff):
            # Obtient la force et le couple générés par les propulseurs du satellite
            F, C = self.get_thrust()
            # Force :
            # Calcul de l'accélération en ajoutant l'accélération gravitationnelle et la force divisée par la masse
            self.a = self.get_ag(planets=planets) + F / self.mass
            self.x, self.v, self.a = self.simulator.integrate(f=self.x, df=self.v, ddf=self.a)
            self.radius, self.speed = None, None
            # Couple :
            # Calcul de l'accélération angulaire en divisant le couple par l'inertie
            self.a_ang = C / self.inertia
            delta_ang = self.x_ang.copy()   # Sauvegarde de l'ancienne valeur
            self.x_ang, self.v_ang, self.a_ang = self.simulator.integrate(f=self.x_ang, df=self.v_ang, ddf=self.a_ang)
            delta_ang = self.x_ang - delta_ang
            # Mise à jour des axes du satellite
            self.get_axes(dalpha=delta_ang)
            if not (self.islanded or self.istakingoff):
                # Vérifie s'il y a eu une collision avec une planète
                self.check_for_collision(planets=planets)
        # Mise à jour des contrôles du satellite
        self.update_controls(infos=infos)

    def update_controls(self, infos=0):
        """
        Met à jour les contrôles du satellite.

        :param infos: (int) Niveau d'informations à afficher.
        """
        for controler in self.controls.keys():
            for step in self.controls[controler]:  # step = (time, value)
                time, value = step[0], step[1]
                if self.simulator.time >= time:
                    if infos:
                        print(f"   | set {controler} to {value}" + ' '*3 + f"({self.simulator.time} sec)")
                    # Gestion des différents types de contrôleurs
                    if '-' in controler:
                        if controler[:8] == 'thruster':
                            # Activation du propulseur correspondant
                            self.get(controler[9:]).on(power=value)
                        if controler[:3] == 'ctr':
                            if controler[4:7] == 'run':
                                getattr(self.controler, controler[8:])(value)   # Run function with args
                            else:
                                setattr(self.controler, controler[4:], value)
                    else:
                        setattr(self, controler, value)
                    self.controls[controler].remove(step)

    def plot(self, fig=None, ax=None, display=True, direction=True):
        """
        Trace la représentation graphique du satellite.

        :param fig: (Figure, optional) Objet Figure de matplotlib.
        :param ax: (Axes3D, optional) Objet Axes3D de matplotlib.
        :param display: (bool, optional) True si le graphique doit être affiché, False sinon.
        :param direction: (bool, optional) True si le vecteur de direction doit être tracé, False sinon.
        :return: (Figure, Axes3D) Objet Figure et Axes3D de matplotlib.
        """
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

        # Vecteur direction
        if direction:
            dir = np.array([self.x, self.x - self.ux * self.size[0]])
            ax.plot(dir[:, 0], dir[:, 1], dir[:, 2], '-k')

        # Affichage
        if display:
            ax.axis('equal')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            plt.show()

        return fig, ax
