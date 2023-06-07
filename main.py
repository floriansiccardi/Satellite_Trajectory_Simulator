from simulator import Simulator
from planet import Planet
from satellite import Satellite

simu = Simulator()
simu.add(Planet(name='Terre'))
simu.add(Satellite(name='ISS'))
