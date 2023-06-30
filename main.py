from classes.simulator import Simulator
from classes.planet import Planet
from classes.satellite import Satellite
from classes.thruster import Thruster
from classes.controler import Controler
from classes.LecteurYAML import LecteurYAML

# On prévient l'utilisateur de remplir le fichier yaml
name = "donnees"
print(f"Afin de pouvoir personaliser les résultats de la simulation, merci de bien vouloir compléter le fichier "
      f"{name}.yaml disponible dans le même dossier que ce script.")
# Récupération du fichier yaml
# Creation un objet YAML au sein duquel on charge une instance de LecteurYAML qui lit le fichier "donnees.yamL"
parser = LecteurYAML('donnees.yaml')
# On exécute la fonction read_yaml() de notre objet LecteurYAML
parsed_data = parser.read_yaml()

# Validation des champs du fichiers yaml
for key, value in parsed_data.items():
    if key == "time" or key == "temps_simu" or key == "pas":
        parser.validate_numeric_value_int(key, value)
    if key == "satellite":
        parser.validate_numeric_value_int_float('poids', parsed_data[key]['poids'])
        for element in parsed_data[key]['taille']:
            parser.validate_numeric_value_int_float('taille', element)
    else:
        parser.validate_numeric_value_int_float(key, value)

# Vérification de la condition time < temps_simu
parser.inferiorite("time", "temps_simu", parsed_data["time"], parsed_data["temps_simu"])

# Création du simulateur, avec possibilité de changer le pas de temps (par défaut 20)
simu = Simulator(dt=20)

# Ajout de la planète Terre :
simu.add(Planet(name='Terre', radius=6371*10**3, mass=5.972*10**24))

# Ajout (optionel) de l'ISS (en vert) :
#simu.add(Satellite(name='ISS', mass=450000, size=(108, 75, 45),
#                   x=(0, simu.get('Terre').radius+408*10**3, 0), v=(-7777.78, 0, 0)))
#simu.get('ISS').set_scale(scale=5000)


# Création de notre satellite mySat (en rouge) :
mySat = Satellite(name='mySat', mass=parsed_data['satellite']['poids'], x=(simu.get('Terre').radius, 0, 0),
                  size=parsed_data['satellite']['taille'], planet_ref=simu.get('Terre'))
# Ajout de thrusters automatiquement, selon la masse du satellite (possibilité de les faire manuellement)
mySat.add('auto_build_thrusters')
# On considère le satellite au sol au début, et on lui applique une couleur rouge pour le distinguer graphiquement
mySat.islanded, mySat.color = True, 'r'
# Augmentation de la taille sur les graphiques (ne change pas les caractéristiques mécaniques)
mySat.set_scale(scale=200000)

# Contrôles automatiques du satellite, par le Controleur :
mySat.controls = {'ctr-run-takeoff': [(60, {})],
                  'ctr-run-geo': [(120, {'radius': parsed_data['rayon_init']})],
                  'ctr-run-homhann': [(parsed_data['time'], {'radius': parsed_data['rayon_fin']})]}

# Une fois le satellite construit, on l'ajoute à la simulation
simu.add(mySat)

# Lancement de la simulation, pour une durée max de 15 sec de calcul OU 20.000 sec dans la simulation
simu.run(duration_max=30, time_max=parsed_data['temps_simu'], infos=1/10)       # On affiche les infos tous les 10%
simu.animation(step=parsed_data['pas'])                                         # Mise en animation des résultats, avec accélération xpas
simu.plot(add={'circle': [parsed_data['rayon_init'], parsed_data['rayon_fin']]})# Affichage de la trajectoire finale, depuis le temps initial

# Graphiques de l'évolutions des puissances des thrusters, du rayon et de la vitesse au cours du temps
simu.graph(x='time', y='power')
simu.graph(x='time', y='r')
simu.graph(x='time', y='v')