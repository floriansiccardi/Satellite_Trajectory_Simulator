import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from classes.planet import Planet
from classes.satellite import Satellite
from classes.saver import Saver
from classes.tools import euler
from time import time
from datetime import timedelta


class Simulator:

    def __init__(self, dt=20):
        """
        Initialise un objet de la classe simulation.

        :param dt: Interval de temps entre chaque itération de simulation en secondes (par défaut 20 sec).
        :type dt: float
        """
        self.dt = dt # Intervalle de temps
        self.running = False # Indicateur d'exécution de la simulation
        self.iteration = 0 # Nombre d'itérations de simulation effectuées

        # Entités :
        self.satellites = [] # Liste des satellites présents dans la simulation
        self.planets = [] # Liste des planètes présentes dans la simulation
        self.saves = Saver()
        self.saves_u = {}

        self.t0 = None # Temps initial de la simulation
        self.time = 0 # Temps écoulé depuis le début de la simulation

        self.controls = {}

    def add(self, obj):
        """
        Ajout d'un objet à la simulation.

        :param obj: Objet à ajouter à la simulation.
        :type obj: Class Satellite ou Class Planet.
        """
        if type(obj) == Satellite:
            obj.linkto(simulator=self) # Lie l'objet à la simulation en cours
            self.satellites.append(obj) # Ajout du Satellite à la liste des satellites de la simulation
            self.saves.save(obj)
            self.saves_u[obj.name] = [obj.ux, obj.uy, obj.uz]
            if not obj.controler is None:
                obj.controler.load(sat=obj)
        elif type(obj) == Planet:
            obj.linkto(simulator=self) # Lie la planète à la simulation en cours
            self.planets.append(obj) # Ajout de la Planète à la liste des planètes de la simulation
        else:
            print(f" > Impossible d'ajouter ce type d'objet à la simulation")

    def get(self, name):
        """
        Récupère un objet de la simulation par son nom.

        :param name: Nom de l'objet à récupérer.
        :type name: string
        :return: Objet correspondant au nom donné, None si rien n'a été trouvé.
        :rtype: Class Planet or Class Satellite
        """
        # Parcours les listes des satellites et des planètes
        for entities in [self.satellites, self.planets]:
            # Parcours chaque objet dans la liste
            for ent in entities:
                # Si le nom de l'objet correspond au nom recherché
                if ent.name == name:
                    # Retourne l'objet
                    return ent
        # Si aucun objet correspondant au nom n'a été trouvé, retourne None
        return None

    def integrate(self, f, df, ddf):
        """
        Effectue l'intégration numérique d'une fonction à l'aide de la méthode désirée.

        :param f: Valeur de la fonction à intégrer.
        :type f: float or 1D-array
        :param df: Valeur de la dérivée de la fonction.
        :type df: float or 1D-array
        :param ddf: Valeur de la dérivée seconde de la fonction.
        :type ddf: float or 1D-array
        :return: Résultat de l'intégration numérique.
        :rtype: float or 1D-array
        """
        return euler(f, df, ddf, self.dt)

    def count_alive(self):
        """
        Compte le nombre de satellites en vie dans la simulation.

        :return: Nombre de satellites en vie.
        :rtype: int
        """
        # Initailisation du compte à 0
        count = 0
        for sat in self.satellites:
            count += sat.alive
        return count

    def run(self, duration_max=60, time_max=10**6, infos=0):
        """
        Exécute la simulation pour une durée maximale donnée ou jusqu'à ce que certaines conditions soient remplies.

        :param duration_max: Durée maximale de la simulation en secondes.
        :type duration_max: float
        :param time_max: Temps maximal de la simulation en secondes.
        :type time_max: float
        :param infos: Fréquence d'affichage des informations pendant la simulation. Peut être défini comme une fraction
                    (ex: 1/X) pour afficher uniquement X fois des informations durant la simulation.
        :type infos: int or float
        :return: True si la simulation s'est terminée normalement, False si tous les satellite sont morts.
        :rtype: boolean
        """
        print(f"\n > Start simulation ...")

        self.running = True
        self.t0 = time()
        # Calcul de la fréquence d'affichage des informations, dans le cas de infos = fraction.
        if infos < 1:
            infos = round(infos * time_max)
        next_info = 0

        while self.running:
            # Réalise une itération de simulation
            self.step(infos)
            # Affichage des informations, si nécessaire
            if infos and self.time >= next_info:
                next_info += infos
                for sat in self.satellites:
                    if not sat.planet_ref is None:
                        print(f"\n - [{sat.name} - {self.time} sec] Altitude : {round(sat.get_altitude())} m, Vitesse : {round(np.linalg.norm(sat.v))} m/s")

            self.iteration += 1

            # Vérification des conditions d'arrêt de la simulation
            if time()-self.t0 >= duration_max or self.time >= time_max or self.count_alive() == 0:
                self.stop()
                return False
        return True

    def step(self, infos=False):
        """
        Effectue une avancée dans la simulation en faisant avancer chaque satellite d'un pas de temps.

        :param infos: Si True, affiche les informations de chaque satellite. Si False, n'affiche pas les informations.
        :type infos: boolean
        """
        # Avance chaque satellite d'un pas de temps
        for sat in self.satellites:
            sat.step(planets=self.planets, infos=infos)
            self.saves.save(sat)
            self.saves_u[sat.name].append([sat.ux, sat.uy, sat.uz])
        # Mise à jour le temps de la simulation
        self.time += self.dt

        # Contrôles manuels pour l'étape suivante
        for ctrl in self.controls.keys():
            for step in self.controls[ctrl]:  # step = (time, value)
                time, value = step[0], step[1]
                if self.time >= time:
                    if infos:
                        print(f"   | set {ctrl} to {value}" + ' '*3 + f"({self.time} sec)")
                        setattr(self, ctrl, value)
                    self.controls[ctrl].remove(step)
        # Contrôles automatiques pour l'étape suivante
        for sat in self.satellites:
            if not sat.controler is None:
                sat.controler.update()

    def stop(self):
        """
        Arrête la simulation et affiche les informations de fin.
        """
        # Arrêt de la simulation
        self.running = False
        # Affiche les informations de fin
        print(f"\n" + '-'*70 + "\n")
        print(f"   Fin de simuation après {self.iteration} itérations et {round(time() - self.t0, 2)} sec")
        print(f"   Durée simulée : {timedelta(seconds=self.iteration * self.dt)}\n\n" + '-'*70 + "\n")

    def plot(self, trajectory=True, add={}):
        """
        Trace le graphique de la simulation en affichant les planètes, satellites et trajectoires des satellites.

        :param trajectory: Si True, affiche les trajectoires des satellites.
                           Si False, n'affiche pas les trajectoires des satellites.
        :type trajectory: boolean
        :param add: Liste des formes à afficher :
                    - 'circle': [r1, r2, ...]
        :type add: dict[list[float]]
        """
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for pln in self.planets:
            fig, ax = pln.plot(fig=fig, ax=ax, display=False)
        for sat in self.satellites:
            fig, ax = sat.plot(fig=fig, ax=ax, display=False)
            if trajectory:
                x = self.saves[sat.name][['x1', 'x2', 'x3']]
                ax.plot(x['x1'], x['x2'], x['x3'], '-' + sat.color)
        if add:
            for type in add.keys():
                if type == 'circle':
                    theta = np.linspace(0, 2 * np.pi, 100)
                    for r in add[type]:
                        ax.plot(r * np.cos(theta), r * np.sin(theta), ':k')
        ax.axis('equal')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.show()

    def animation(self, trajectory=True, step=1):
        """
        Anime la simulation en affichant une séquence de graphiques représentant l'évolution des positions des planètes
        et des satellites.

        :param trajectory: Si True, affiche les trajectoires des satellites.
                           Si False, n'affiche pas les trajectoires des satellites.
        :type trajectory: boolean
        :param step: Définit le nombre d'itérations entre chaque graphique affiché.
                     Par défaut, pas de 1, ce qui signifie qu'un graphique est affiché à chaque itération.
                     Une valeur plus élevée de `step` réduit le nombre total de graphiques affichés.
        :type step: int
        """
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        for i in range(0, self.iteration, step):
            # Efface le contenu de la figure pour le graphique suivant
            plt.cla()
            ax.axis('equal')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')

            # Trace les planètes
            for pln in self.planets:
                fig, ax = pln.plot(fig=fig, ax=ax, display=False)
            # Trace les satellites
            for sat in self.satellites:
                x = self.saves[sat.name][['x1', 'x2', 'x3']][0:i+1]
                sat.x = np.array([x['x1'].iloc[-1], x['x2'].iloc[-1], x['x3'].iloc[-1]])
                sat.ux, sat.uy, sat.uz = self.saves_u[sat.name][i]
                fig, ax = sat.plot(fig=fig, ax=ax, display=False)
                if trajectory:
                    # Trace la trajectoire du satellite jusqu'à l'itération actuelle
                    ax.plot(x['x1'], x['x2'], x['x3'], '-' + sat.color)
            # Pause pour permettre l'affichage du graphique
            plt.pause(0.01)
        plt.show()

    def graph(self, y, x='time', scaled=True, sat=None):
        """
        Affiche le graphique de la donnée x en fonction de y, pour le satellite désiré.

        :param y: Nom de la donnée en ordonnée
        :type y: string
        :param x: Nom de la donnée en absice (par défaut 'time')
        :type x: sting
        :param scaled: Dans le cas d'un graphique à plusieurs fonctions, normalise les fonctions pour qu'elles soient
                       toutes affichées correctement (par défaut True).
        :type scaled: boolean
        :param sat: Nom du satellite désiré (Si None, prend le 1er dans la liste)
        :type sat: string
        """
        if sat is None:
            sat = self.satellites[0].name
        self.saves.plot(x=x, y=y, sat=sat, scaled=scaled)
