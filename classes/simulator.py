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

        :param dt: (float, optional) Interval de temps entre chaque itération de simulation en secondes.
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

        :param obj: (Object) Objet à ajouter à la simulation.
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

        :param name: (str) Nom de l'objet à récupérer.
        :return: (Object) Objet correspondant au nom donné, None si rien n'a été trouvé.
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
        Effectue l'intégration numérique d'une fonction à l'aide de la méthode d'Euler.

        :param f: (float) Valeur de la fonction à intégrer.
        :param df: (float) Valeur de la dérivée de la fonction.
        :param ddf: (float) Valeur de la dérivée seconde de la fonction.
        :return: (float) Résultat de l'intégration numérique.
        """
        return euler(f, df, ddf, self.dt)

    def count_alive(self):
        """
        Compte le nombre de satellites en vie dans la simulation.

        :return: (int) Nombre de satellites en vie.
        """
        # Initailisation du compte à 0
        count = 0
        for sat in self.satellites:
            count += sat.alive
        return count

    def run(self, duration_max=60, time_max=10**6, infos=0):
        """
        Exécute la simulation pour une durée maximale donnée ou jusqu'à ce que certaines conditions soient remplies.

        :param duration_max: (float, optional) Durée maximale de la simulation en secondes.
        :param time_max: (float, optional) Temps maximal de la simulation en secondes.
        :param infos: (int, optional) Fréquence d'affichage des informations pendant la simulation.
        :return: (bool) True si la simulation s'est terminée normalement, False sinon.
        """
        print(f"\n > Start simulation ...")

        self.running = True
        self.t0 = time()
        # Calcul de la fréquence d'affichage des informations
        if infos < 1:
            infos = round(infos * time_max)
        next_info = 0

        while self.running:
            self.step(infos)
            # Affichage des informations
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

        :param infos: (bool, optional) Si True, affiche les informations de chaque satellite.
                             Si False, n'affiche pas les informations.
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

        :param trajectory: (bool, optional) Si True, affiche les trajectoires des satellites.
                                            Si False, n'affiche pas les trajectoires des satellites.
        :param add: (dict, optional) Liste des cercles à afficher.
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

        :param trajectory: (bool, optional) Si True, affiche les trajectoires des satellites.
                                            Si False, n'affiche pas les trajectoires des satellites.
        :param step: (int, optional) Pas de l'animation. Définit le nombre d'itérations entre chaque graphique affiché.
                     Par défaut, pas de 1, ce qui signifie qu'un graphique est affiché à chaque itération.
                     Une valeur plus élevée de `step` réduit le nombre total de graphiques affichés.
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

    def graph(self, y, x='time', scaled=False, sat=None):
        if sat is None:
            sat = self.satellites[0].name
        self.saves.plot(x=x, y=y, sat=sat, scaled=scaled)
