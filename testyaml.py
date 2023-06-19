from simulator import Simulator
from planet import Planet
from satellite import Satellite
from thruster import Thruster
from controlers import Controler
from LecteurYAML import LecteurYAML
import numpy as np

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
    if key == "time" or key == "temps_simu":
        parser.validate_numeric_value_int(key, value)
    if key == "satellite":
        parser.validate_numeric_value_int_float('poids', parsed_data[key]['poids'])
        for element in parsed_data[key]['taille']:
            parser.validate_numeric_value_int_float('taille', element)
    else:
        parser.validate_numeric_value_int_float(key, value)

simu = Simulator()
simu.controls = {'dt': [(1150, 5), (2750, 20)]}

# --- Terre :
simu.add(Planet(name='Terre', radius=6371*10**3, mass=5.972*10**24))

# --- ISS (vert) :
#simu.add(Satellite(name='ISS', mass=450000, size=(108, 75, 45),
#                   x=(0, simu.get('Terre').radius+408*10**3, 0), v=(-7777.78, 0, 0)))
#simu.get('ISS').set_scale(scale=5000)


# --- mySat (rouge) :
mySat = Satellite(name='mySat', mass=parsed_data['satellite']['poids'], x=(simu.get('Terre').radius, 0, 0),
                  size=parsed_data['satellite']['taille'], planet_ref=simu.get('Terre'))
mySat.add(Thruster(xr=(-mySat.size[0]/2, 0, 0), thrust_max=parsed_data['thuster_principal'], axe='xp', name='main'))
mySat.add(Thruster(xr=(-mySat.size[0]/3, mySat.size[1]/2, 0), thrust_max=50, axe='ym', name='left'))
mySat.add(Thruster(xr=(-mySat.size[0]/3, -mySat.size[1]/2, 0), thrust_max=50, axe='yp', name='right'))
mySat.add(Thruster(xr=(mySat.size[0]/2, 0, 0), thrust_max=parsed_data['thuster_brake'], axe='xm', name='brake'))

mySat.islanded, mySat.color = True, 'r'
mySat.set_scale(scale=200000)
# Contrôles manuels pour lancer sur une orbite temporaire
mySat.controls = {'thruster-main': [(60, 0.79)],
                  'thruster-left': [(1200, 0.014), (1205, 0.), (1400, 0.022), (1405, 0.)],
                  'thruster-right': [(2700, 0.009), (2720, 0.)],
                  'islanded': [(60, False)], 'istakingoff': [(60, True), (120, False)],
                  'ctr-reach_geo': [(1200, parsed_data['rayon_init'])],
                  'ctr-run-synchronize': [(2800, {})],
                  'ctr-run-homhann': [(parsed_data['time'], {'radius': parsed_data['rayon_fin']})]}
# Pilote automatique pour les changement d'orbites
mySat.add(Controler(sat=mySat))

simu.add(mySat)

simu.run(duration_max=10, time_max=parsed_data['temps_simu'], infos=1/10)
simu.plot(add={'circle': [parsed_data['rayon_init'], parsed_data['rayon_fin']]})
# simu.animation(step=3)