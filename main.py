from simulator import Simulator
from planet import Planet
from satellite import Satellite
from thruster import Thruster
import numpy as np

simu = Simulator()

# Terre :
simu.add(Planet(name='Terre', radius=6371*10**3, mass=5.972*10**24))

# ISS :
simu.add(Satellite(name='ISS', mass=450000, size=(108, 75, 45),
                   x=(0, simu.get('Terre').radius+408*10**3, 0), v=(-7777.78, 0, 0)))
simu.get('ISS').set_scale(scale=2000)

# mySat :
mySat = Satellite(name='mySat', mass=10000, x=(simu.get('Terre').radius, 0, 0),
                  size=(3, 1, 1), planet_ref=simu.get('Terre'))
mySat.add(Thruster(xr=(-mySat.size[0]/2, 0, 0), thrust_max=98500, axe='xp', name='main'))
mySat.add(Thruster(xr=(-mySat.size[0]/3, mySat.size[1]/2, 0), thrust_max=10, axe='ym', name='left'))
mySat.add(Thruster(xr=(-mySat.size[0]/3, -mySat.size[1]/2, 0), thrust_max=10, axe='yp', name='right'))
mySat.islanded, mySat.color = True, 'r'
mySat.set_scale(scale=200000)

mySat.controls = {
    'thruster-main': [(10, 1.), (162, 0.95), (170, 0.3), (200, 0.)],
    'thruster-left': [(120, 0.08), (121, 0.)],
    'thruster-right': [(160, 0.05), (161, 0.)],
    'islanded': [(10, False)], 'istakingoff': [(10, True), (100, False)],
}
simu.add(mySat)

#simu.run(time_max=10, iteration_max=1000, infos=50)
#simu.plot()
#simu.animation(step=5)
