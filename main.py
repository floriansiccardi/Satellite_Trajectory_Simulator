from simulator import Simulator
from planet import Planet
from satellite import Satellite

simu = Simulator()
simu.add(Planet(name='Terre', radius=6371, mass=5.972*10**24))
simu.add(Satellite(name='ISS', mass=420000, x=(1.2*simu.get('Terre').radius, 0, 0)))
simu.get('ISS').plot()
simu.show()