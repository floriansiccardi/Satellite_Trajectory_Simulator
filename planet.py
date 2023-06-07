from random import randint


class Planet:

    def __init__(self, name=''):

        # Identification :
        self.id = randint(0, 99999)
        self.name = name

    def __eq__(self, other):
        return self.id == other.id
