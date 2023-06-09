from simulator import Simulator
from planet import Planet
from satellite import Satellite

simu = Simulator()
simu.add(Planet(name='Terre', radius=6371*10**3, mass=5.972*10**24))
simu.add(Satellite(name='ISS', mass=450000, size=(108, 75, 45),
                   x=(0, simu.get('Terre').radius+408*10**3, 0), v=(-7777.78, 0, 0)))
#simu.add(Satellite(name='mySat', mass=420000, x=(simu.get('Terre').radius, 0, 0), size=(3, 1, 1)))
simu.get('ISS').set_scale(scale=2000)
#simu.get('mySat').set_scale(scale=20000)

simu.run(time_max=30, iteration_max=289)
simu.trajectory()