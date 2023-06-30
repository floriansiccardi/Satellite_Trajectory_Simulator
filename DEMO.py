from classes.simulator import Simulator
from classes.planet import Planet
from classes.satellite import Satellite
from classes.thruster import Thruster
from classes.controler import Controler
import numpy as np

# Création du simulateur, avec possibilité de changer le pas de temps (par défaut 20)
simu = Simulator(dt=20)

# Ajout de la planète Terre :
simu.add(Planet(name='Terre', radius=6371*10**3, mass=5.972*10**24))

# Ajout (optionel) de l'ISS (en vert) :
#simu.add(Satellite(name='ISS', mass=450000, size=(108, 75, 45),
#                   x=(0, simu.get('Terre').radius+408*10**3, 0), v=(-7777.78, 0, 0)))
#simu.get('ISS').set_scale(scale=5000)

# Création de notre satellite mySat (en rouge) :
mySat = Satellite(name='mySat', mass=1000, x=(simu.get('Terre').radius, 0, 0),
                  size=(3, 1, 1), planet_ref=simu.get('Terre'))
# Ajout de thrusters automatiquement, selon la masse du satellite (possibilité de les faire manuellement)
mySat.add('auto_build_thrusters')
# On considère le satellite au sol au début, et on lui applique une couleur rouge pour le distinguer graphiquement
mySat.islanded, mySat.color = True, 'r'
# Augmentation de la taille sur les graphiques (ne change pas les caractéristiques mécaniques)
mySat.set_scale(scale=200000)
# Contrôles automatiques du satellite, par le Controleur :
mySat.controls = {'ctr-run-takeoff': [(60, {})],                        # Décollage à 60 sec
                  'ctr-run-geo': [(120, {'radius': 9*10**6})],          # Approche de la GEO à 9.000km après 120 sec
                  'ctr-run-homhann': [(10000, {'radius': 12*10**6})]}   # Transfert d'Hohmann vers 12.000km à 10k sec
# Une fois le satellite construit, on l'ajoute à la simulation
simu.add(mySat)

# Lancement de la simulation, pour une durée max de 15 sec de calcul OU 20.000 sec dans la simulation
simu.run(duration_max=15, time_max=20000, infos=1/10)   # On affiche les infos tous les 10%
simu.plot(add={'circle': [9*10**6, 12*10**6]})          # Affichage de la trajectoire finale, depuis le temps initial
#simu.animation(step=3)                                 # Mise en animation des résultats, avec accélération x3

# Graphiques de l'évolutions des puissances des thrusters, du rayon et de la vitesse au cours du temps
simu.graph(x='time', y='power')
simu.graph(x='time', y='r')
simu.graph(x='time', y='v')
