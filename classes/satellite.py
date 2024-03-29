import numpy as np
import matplotlib.pyplot as plt
from classes.tools import zero, rotation_matrix, from_other_base
from classes.thruster import Thruster
from classes.controler import Controler
from classes.object import Object


class Satellite(Object):

    def __init__(self, mass, name='unnamed', x=(0, 0, 0), v=(0, 0, 0), a=(0, 0, 0), size=(1, 1, 1), planet_ref=None):
        """
        Initialise un objet de la classe satellite.
        Comporte les aspect de la classe Object, en y ajoutant une taille et une planète de référence, ainsi qu'un grand
        nombre de fonctionnalitées.

        :param mass: Masse de l'objet.
        :type mass: float
        :param name: Nom de l'objet (par défaut 'unnamed').
        :type name: str
        :param x: Coordonnées spatiales de l'objet (par défaut (0, 0, 0)).
        :type x: 1D-array or tuple   (3 components)
        :param v: Vitesse de l'objet (par défaut (0, 0, 0)).
        :type v: 1D-array or tuple   (3 components)
        :param a: Accélération de l'objet (par défaut (0, 0, 0)).
        :type a: 1D-array or tuple   (3 components)
        :param size: Taille du satellite (par défaut (1, 1, 1)).
        :type size: 1D-array or tuple   (3 components)
        :param planet_ref: Référence à la planète associée au satellite (par défaut None).
        :type planet_ref: Class Planet
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

        # Thrusters
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

        :param scale: Échelle sur le graphique.
        :type scale: float
        """
        self.scale = scale
        self.size = np.dot(scale, self.size)

    def set_planet_ref(self, planet_ref):
        """
        Définit la référence planétaire pour le satellite (pour le calcul de rayon, du vcteur ur, des orbites GEO ...)

        :param planet_ref: Planète de référence pour le satellite.
        :type planet_ref: Class Planet
        """
        self.planet_ref = planet_ref

    def add(self, obj):
        """
        Ajoute un objet au satellite (cela peut être un thruster ou un controleur).
        Pour ajouter automatiquement une configuration de thruster prédéfinis, entrer en argument
        'auto_build_thrusters'. Cela va définir 1 propulseur principal, 1 frein, et 2 propulseurs latéraux, selon la
        masse du satellite.

        :param obj: Objet à ajouter.
        :type obj: Class Thruster or Class Controler or string
        """
        if type(obj) == Thruster: # Si l'objet est de type Thruster
            # Ajoute le thruster à la liste des thrusters du satellite
            self.thrusters.append(obj)
        elif type(obj) == Controler: # Si l'objet est de type Controler
            # Définit le controleur pour le satellite
            self.controler = obj
            self.controler.load(sat=self)
        elif obj == 'auto_build_thrusters': # Si l'utilisateur souhaite automatiquement ajouter les thrusters
            self.add(Thruster(xr=(-self.size[0] / 2, 0, 0), thrust_max=12 * self.mass, axe='xp', name='main'))
            self.add(Thruster(xr=(-self.size[0] / 3, self.size[1] / 2, 0), thrust_max=self.mass / 200, axe='ym',
                               name='left'))
            self.add(Thruster(xr=(-self.size[0] / 3, -self.size[1] / 2, 0), thrust_max=self.mass / 200, axe='yp',
                               name='right'))
            self.add(Thruster(xr=(-self.size[0] / 2, 0, 0), thrust_max=self.mass, axe='xp', name='brake'))
        else:
            print(f" > Impossible d'ajouter ce type d'objet à la simulation")

    def get(self, name):
        """
        Récupère un thruster du satellite par son nom.

        :param name: Nom du thruster à récupérer.
        :type name: string
        :return: Thruster correspondant au nom spécifié, None s'il n'est pas trouvé.
        :rtype: Class Thruster
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

        :return: Altitude du satellite en mètres.
        :rtype: float
        """
        # Vérifie qu'une planète de référence soit bien spécifiée
        if self.planet_ref is None:
            print(f" /!\\ Aucune planète référence n'a été donné. L'altitude retournée est donc nulle")
            return 0 # Si aucune planète de référence, retourner une altitude de 0
        return np.linalg.norm(self.x - self.planet_ref.x) - self.planet_ref.radius

    def get_axes(self, dalpha=(0, 0, 0)):
        """
        Calcule et retourne les vecteurs de base des axes du satellite après une rotation.

        :param dalpha: Les angles de rotation autour de chaque axe (en radians).
        :type dalpha: 1D-array or tuple   (3 components)
        :return: Les vecteurs de base des axes du satellite après la rotation.
        :rtype: tuple   (3 * 1D-array, 3 components for each)
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

        :return: Force totale et couple total générés par les thrusters du satellite.
        :rtype: tuple   (2 * 1D-array, 3 components for each)
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

        :return: Rayon entre le satellite et à sa planète de référence.
        :rtype: float
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

        :return: Vitesse du satellite.
        :rtype: float
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

        :param planets: Liste des planètes présentes dans la simulation.
        :type planets: list[Class Planet]
        :param infos: Quantité d'informations à afficher (toutes les 'infos' étapes. Si 0, affiche aucune infos).
        :type infos: int
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

        :param infos: Quantité d'informations à afficher (toutes les 'infos' étapes. Si 0, affiche aucune infos).
        :type infos: int
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
        Trace la représentation en 3D du satellite.

        :param fig: Objet de la figure matplotlib (Si None, création d'une nouvelle).
        :type fig: figure    (from matplotlib)
        :param ax: Objet des axes matplotlib en 3D (Si None, création d'une nouvelle).
        :type ax: axe    (from matplotlib)
        :param display: Indique si le tracé doit être affiché (par défaut True).
        :type display: boolean
        :param direction: Affiche ou non le vecteur directeur du satellite (par défaut True).
        :type direction: boolean
        :return: Figure et des axes matplotlib mis à jour.
        :rtype: figure, axe    (from matplotlib)
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
