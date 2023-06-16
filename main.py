from simulator import Simulator
from planet import Planet
from satellite import Satellite
from thruster import Thruster
from controlers import Controler
import numpy as np

simu = Simulator()
simu.controls = {'dt': [(1150, 5), (3000, 50)]}

# --- Terre :
simu.add(Planet(name='Terre', radius=6371*10**3, mass=5.972*10**24))

# --- ISS (vert) :
#simu.add(Satellite(name='ISS', mass=450000, size=(108, 75, 45),
#                   x=(0, simu.get('Terre').radius+408*10**3, 0), v=(-7777.78, 0, 0)))
#simu.get('ISS').set_scale(scale=5000)

# --- mySat (rouge) :
mySat = Satellite(name='mySat', mass=10000, x=(simu.get('Terre').radius, 0, 0),
                  size=(3, 1, 1), planet_ref=simu.get('Terre'))
mySat.add(Thruster(xr=(-mySat.size[0]/2, 0, 0), thrust_max=125000, axe='xp', name='main'))
mySat.add(Thruster(xr=(-mySat.size[0]/3, mySat.size[1]/2, 0), thrust_max=50, axe='ym', name='left'))
mySat.add(Thruster(xr=(-mySat.size[0]/3, -mySat.size[1]/2, 0), thrust_max=50, axe='yp', name='right'))
mySat.islanded, mySat.color = True, 'r'
mySat.set_scale(scale=200000)
# Contrôles manuels pour lancer sur une orbite temporaire
mySat.controls = {'thruster-main': [(60, 0.79)],
                  'thruster-left': [(1200, 0.014), (1205, 0.), (1400, 0.022), (1405, 0.)],
                  'thruster-right': [],
                  'islanded': [(60, False)], 'istakingoff': [(60, True), (120, False)],
                  'ctr-reach_geo': [(1200, 8*10**6)]}
# Pilote automatique pour les changement d'orbites
mySat.add(Controler(sat=mySat))

simu.add(mySat)

simu.run(duration_max=10, time_max=10000, infos=1/6)
simu.plot(radius=[8*10**6])
#simu.animation(step=3)

print(simu.get('mySat').get('main').power)
