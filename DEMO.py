from classes.simulator import Simulator
from classes.planet import Planet
from classes.satellite import Satellite
from classes.thruster import Thruster
from classes.controler import Controler
import numpy as np

simu = Simulator(dt=20)

# --- Terre :
simu.add(Planet(name='Terre', radius=6371*10**3, mass=5.972*10**24))

# --- ISS (vert) :
#simu.add(Satellite(name='ISS', mass=450000, size=(108, 75, 45),
#                   x=(0, simu.get('Terre').radius+408*10**3, 0), v=(-7777.78, 0, 0)))
#simu.get('ISS').set_scale(scale=5000)

# --- mySat (rouge) :
mySat = Satellite(name='mySat', mass=1000, x=(simu.get('Terre').radius, 0, 0),
                  size=(3, 1, 1), planet_ref=simu.get('Terre'))
mySat.add('auto_build_thrusters')
mySat.islanded, mySat.color = True, 'r'
mySat.set_scale(scale=200000)
# Contrôles manuels pour lancer sur une orbite temporaire
mySat.controls = {'ctr-run-takeoff': [(60, {})],
                  'ctr-run-geo': [(120, {'radius': 9*10**6})],
                  'ctr-run-homhann': [(10000, {'radius': 12*10**6})]}
simu.add(mySat)


simu.run(duration_max=30, time_max=20000, infos=1/10)
simu.plot(add={'circle': [9*10**6, 12*10**6]})
#simu.animation(step=5)


simu.graph(x='time', y='power')
simu.graph(x='time', y='r')
simu.graph(x='time', y='v')
