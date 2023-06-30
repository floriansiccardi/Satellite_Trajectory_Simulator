import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Saver:

    def __init__(self):
        """
        Initialise la class Saver.
        Permet de sauvegarde un grand nombre de donnée, sous forme de DataFrame, lors de la simulation, puis de les
        afficher sous forme de graphique à la fin de celle-ci.
        """
        # Variables à sauvegarder :
        self.df = pd.DataFrame(columns=['name', 'time', 'r', 'x1', 'x2', 'x3', 'v', 'dt', 'orientation', 'power'])
        # TITRE : Évolution xxxx en fonction yyyy
        self.title = {'time': 'du Temps', 'r': 'du Rayon', 'v': 'de la Vitesse', 'dt': 'du Pas de temps',
                      'orientation': 'de l\'Orientation', 'power': 'des Puissances'}
        self.units = {'time': 'sec', 'r': 'm', 'v': 'm/s', 'dt': 'sec', 'orientation': 'rad', 'power': '%'}

    def __call__(self, *args, **kwargs):
        """
        Affiche le contenue global de la sauvegarde
        """
        print(self.df)

    def __getitem__(self, sat):
        """
        Extrait toutes les sauvgardes d'un satellite en particulier. Si le satellite n'exsite pas dans la base de
        données, retourne None.

        :param sat: Nom du satellite à extraire
        :type sat: string
        :return: Base de données du satellite (s,il existe)
        :rtype: DataFrame   (from pandas)
        """
        if sat in self.df['name'].unique():
            return self.df[self.df['name'] == sat]

    def save(self, sat):
        """
        Aoute uneligne à la base de donnée actuelle, en y sauvegardant les données actuelles du satellite.

        :param sat: Satellite complet
        :type sat: Class Satellite
        """
        # Ajout les données à la fin du DataFrame
        self.df.loc[len(self.df.index)] = [sat.name, sat.simulator.time, sat.get_radius(), sat.x[0], sat.x[1], sat.x[2],
                                           sat.get_speed(), sat.simulator.dt, sat.x_ang[2],
                                           {thruster.name: sat.get(thruster.name).power for thruster in sat.thrusters}]

    def plot(self, sat, y, x='time', scaled=True):
        """
        Affiche le graphique de la donnée x en fonction de y, pour le satellite désiré.

        :param sat: Nom du satellite désiré
        :type sat: string
        :param y: Nom de la donnée en ordonnée
        :type y: string
        :param x: Nom de la donnée en absice (par défaut 'time')
        :type x: sting
        :param scaled: Dans le cas d'un graphique à plusieurs fonctions, normalise les fonctions pour qu'elles soient
                       toutes affichées correctement (par défaut True).
        :type scaled: boolean
        """
        # Colonne x (et y) du DataFrame, uniquement pour le satellite concerné
        dx, dy = self.__getitem__(sat)[x], self.__getitem__(sat)[y]
        # Si plusieurs données sont stockées dans la ligne
        if type(dy[0]) == dict:
            # Nom des fonctions (ou "sous-colonnes")
            keys = dy[0].keys()
            for key in keys:
                save = []
                for row in dy:
                    save.append(row[key])
                m = max(save)   # Pour la normalisation
                if scaled and m != 0 and m != 1:
                    save = [value / m for value in save]    # Normalisation de la fonction
                    plt.plot(dx, save, label=key + f'   (x{round(1/m)})')
                else:
                    plt.plot(dx, save, label=key)
            plt.legend()
        else:
            plt.plot(dx, dy)
        # Titres et axes
        plt.title(f"Évolution {self.title[y]} ({self.units[y]}) en fonction {self.title[x]} ({self.units[x]})")
        plt.xlabel(f"{self.title[x].split(' ')[-1]} ({self.units[x]})")
        plt.ylabel(f"{self.title[y].split(' ')[-1]} ({self.units[y]})")
        plt.show()
