import numpy as np
from classes.tools import normalize, sign
from math import ceil
"""
Classe Controler, intégré à un satellite, afin d'effectuer des instructions demandés dans l'utilisateur et donc de
réaliser les bonnes commandes pour guider le satellite à la cible désiré.
"""


class Controler:

    def __init__(self, sat=None):
        """
        Initilisation de la classe Controler (constantes physiques, séries d'instructions ...)

        :param sat: Satellite auquel s'applique le contrôleur
        :type sat: Class Satellite
        """
        # Consatant de gravitation universelle
        self.G = 6.6743015 * 10 ** -11
        self.z = np.array([0, 0, 1])

        # États de contrôles actuels
        self.reach_geo = None   # Commande pous rejoindre une géo précise
        self.reach_sync = None  # Commande pour synchroniser la rotation avec la période orbitale
        self.do_homhann = None  # Commande pour réaliser un transfert d'Hohmann

        # Chargement des données du satellite
        self.load(sat=sat)

    def load(self, sat):
        """
        Charge le satellite désiré dans le contrôleur

        :param sat: Satellite auquel s'applique le contrôleur
        :type sat: Class Satellite
        """
        if not sat is None:
            self.sat = sat
            self.planet = self.sat.planet_ref
            self.simulator = self.sat.simulator

    def geo_speed(self, radius):
        """
        Retourne la vitesse nécessaire pour maintenir l'orbite GEO au rayon demandé

        :param radius: Rayon autour du centre de l'astre (en m)
        :type radius: float
        :return: Vitesse tangentielle (en m/s)
        :rtype: float
        """
        return np.sqrt(self.G * self.planet.mass / radius)

    def get_period(self):
        """
        Calcule la période orbitale actuelle du satellite.

        :return: Période orbitale (en s)
        :rtype: float
        """
        return 2 * np.pi * (np.linalg.norm(self.sat.x - self.planet.x) / np.linalg.norm(self.sat.v))

    def get_homhann_transfert_time(self, r1, r2):
        """
        Calcule le temps nécessaire pour réaliser un transfert de Hohmann (demi-elliptique)

        :param r1: Rayon GÉO de départ (en m)
        :type r1: float
        :param r2: Rayon GÉO d'arrivée (en m)
        :type r2:  float
        :return: Temps de transfert (demi-période elliptique) (en sec)
        :rtype: float
        """
        return 1 / 2 * np.sqrt(4 * np.pi ** 2 / self.G / self.planet.mass * ((r1 + r2) / 2) ** 3)

    def power_for_synchronize_rotation(self, axe=2):
        """
        Retourne la puissance (de 0% à 100%) à appliquer au thruster précisé en sortie, durant n iteration de dt sec,
        afin d'arrêter sa rotation.

        :param axe: Numéro de l'Axe de rotation (0 -> x, 1 -> y, 2 -> z)
        :type axe: int   (0, 1 ou 2)
        :return: - power : Puissance de 0% à 100% du thruster,
                 - n : Nombre d'itération nécessaire à la rotation,
                 - thruster : Nom du thruster à activer.
        :rtype : dict[float]
        """
        # Coefficient nécéssaire pour le choix du thruster (vérifier sa  direction)
        power = - self.sat.v_ang[axe] * self.sat.inertia[axe] / self.simulator.dt
        if power == 0:
            return {'power': 0, 'n': 1, 'thruster': 'main'} # Instructions inutiles, pour ne pas faire crash le sat
        # Essaie de tous les rpopulseurs :
        for thruster in self.sat.thrusters:
            T = thruster.torque_max[axe]    # Couple disponnible dans l'axe voulu
            if T != 0:
                if sign(power) == sign(T):
                    power /= thruster.torque_max[axe]
                    n = ceil(power)
                    return {'power': power / n, 'n': n, 'thruster': thruster.name}

    def geo(self, args={'radius': 0}):
        """
        Ordonne au Contrôleur de réaliser les manoeuvres pour rejoindre l'orbite géo-stationnaire au rayon précisé.
        La manoeuvre se découpe en 2 phases :
            - Accélération radiale uniforme :
                acc = gamma_1 * Poids_sat * ur
            - Maintient de l'accélération radiale, avec rotation sur un côté, afin d'accélérer perpendiculairement :
                acc = gamma_2 * Poids_sat * ur   +   acc_utheta   , où acc_utheta > 0 augmentant au cours du temps
        La seconde phase permet d'accélérer tangentiellement, afin d'aquerir la vitesse nécéssaire pour l'orbite GEO

        :param args: Rayon de l'orbite géo-stationnaire souhaitée (en m)
        :type args: dict[float]
        """
        # Coefficient pour le calcul de l'impulsion latérale (rotation), dépendamment des caractéristiques du satellite
        coef = 1 / self.simulator.dt * (self.sat.inertia[2] / self.sat.get('left').torque_max[2])
        # État de l'instruction (étape, rayon souhaité, coefficients gamma, passage phase 1 vers phase 2, erreurs_max)
        self.reach_geo = {'radius': args['radius'], 'step': 'approach', 'switch_step': 0.80,
                          'gamma_1': 0.025, 'gamma_2': 0.02, 'speed': self.geo_speed(args['radius']),
                          'rot_pulse': 0.0015 * coef,
                          'epsilon': {'radius': 0.02, 'speed': 0.02, 'angle': 0.02}}
        print(f"   | ctr: phase 1 of geo reaching started")

    def takeoff(self, args={}):
        """
        Ordonne au Contrôleur de faire décoller le satellite, à 90% de sa puissance maximale

        :param args: Vide (pour uniformiser la synthaxe)
        :type args: dict (empty)
        """
        self.sat.istakingoff = True
        self.sat.get('main').on(power=0.90)

    def synchronize(self, args={}):
        """
        Ordonne au contrôleur de syncrhoniser la rotation avec la période orbitale, soit, sur une orbite GÉO :
            - Le vecteur ux poitera toujours vers le vecteur vitesse
            - Le vecteur +/- uy poitera toujours vers le centre de la planète de référence
        Créer le dictionnaire d'instruction reach_sync = {'power', 'n', 'thruster', 'step'}.
        La synchronisation est découpée en 3 étapes :
            - stop : Arrête la rotation du satellite (vitesse angulaier nulle)
            - wait : Attends que le vecteur +/- uy pointe vers le centre (à 1% prés)
            - sync : Ajuste la vitesse de rotation pour se synchroniser
        Cette méthode d'arrêt-resynchronisation n'est pas la plus optimale en terme de temps et de carburant, mais il
        s'agit de la moins complexe à implémenter.

        :param args: Vide (pour uniformiser la synthaxe)
        :type args: dict (empty)
        """
        # Calcul de la puissance nécéssaire à la rotation :
        self.reach_sync = self.power_for_synchronize_rotation(axe=2)
        self.reach_sync['step'], self.reach_sync['iteration'] = 'stop', 0
        # Mise en puissance du propulseur concerné :
        self.sat.get(self.reach_sync['thruster']).on(power=self.reach_sync['power'])
        print(f"   | ctr: start to synchronize rotation")

    def homhann(self, args={'radius': 0}):
        """
        Ordonne au contrôleur de réaliser un transfert d'Hohmann du rayon actual au rayon radius désiré en argument.
        Les instructions de transfert sont d'abord calculées, vérifiées puis envoyées, si elles sont valides. Il faut
        donc que les instructions au départ ET à l'arrivée soient physiquement réalisables.
        Créer le dictionnaire d'instruction reach_sync = {'power', 'n', 'thruster', 'stop_at', 'radius', 'rot'}.
            Rot étant un dictionnaire contenant toutes les instructions de mise en rotation du satellite durant
            l'orbite elliptique.

        :param args: Rayon d'arrivé du transfert (en m). Le rayon de départ est le rayon actuel du satellite.
        :type args: dict[float]
        """
        # Rayon de départ et d'arrivée
        r1, r2 = self.sat.get_radius(), args['radius']
        # Vitesses au départ et à l'arrivée (pour rejoindre et quitter l'orbite elliptique)
        v = np.sqrt(np.dot(2 * self.G * self.planet.mass, np.array([1 / r1, 1 / r2]) - 1 / (r1 + r2)))
        # Calcul des puissances nécéssaires au delta de vitesse (départ)
        self.do_homhann = self.power_for_speed(speed=v[0] - self.sat.get_speed())
        # Si la mise en accélération n'est pas possible (dans un lapse de temps maximal)
        if self.do_homhann is None:
            print(f"     ctr: impossible to reach an elliptical orbit")
        else:
            # Calcul du temps de transfert
            self.do_homhann['time'], self.do_homhann['radius'] = self.get_homhann_transfert_time(r1=r1, r2=r2), r2
            # Calcul de la puissance nécéssaire à la rotation :
            data = self.power_for_rotation(period=-2 * self.do_homhann['time'])
            if data is None:
                print(f"   ctr: impossible to reach an elliptical orbit")
            else:
                # Enregistrement du temps auquel le satellite devra rejoindre la GEO
                self.do_homhann['stop_at'] = self.do_homhann['time'] + self.simulator.time
                # power_already_in = Power "déjà comprise dans la alpha_point", donc à ne pas ajouter
                power_already_in = self.power_for_rotation(period=self.get_period())['power']
                # Mise en puissance du propulseur concerné pour la rotation :
                self.sat.get(data['thruster']).on(power=-(data['power'] - power_already_in))
                # Enregistrement des instructions pour la rotation :
                self.do_homhann['rot'] = data
                # Mise ne puissance du propulseur concerné pour la vitesse :
                self.sat.get(self.do_homhann['thruster']).on(power=self.do_homhann['power'])
                # Mise à jour des états actuels
                self.do_homhann['step'], self.do_homhann['iteration'] = 'reach_elliptic', 0

    def power_for_speed(self, speed, direction=(1, 0, 0)):
        """
        Retourne la puissance (de 0% à 100%) à appliquer au thruster précisé en sortie, durant n iteration de dt sec,
        afin d'augmenter sa vitesse de speed dans la direction souhaitée

        :param speed: Écart de vitesse à ajouter (speed = v_fin - v_init)
        :type speed: float
        :param direction: Vecteur directeur normalisé de la direction de la vitesse souhaité
        :type direction: 1D-array (3 dimensions)
        :return: - power : Puissance de 0% à 100% du thruster,
                 - n : Nombre d'itération nécessaire à l'accélération,
                 - thruster : Nom du thruster à activer.
        :rtype : dict[float]
        """
        # Coefficient nécéssaire pour le choix du thruster (vérifier sa  direction)
        power = speed * self.sat.mass / self.simulator.dt
        if power == 0:
            return {'power': 0, 'n': 1, 'thruster': 'main'}
        # Essaie de tous les propulseurs :
        for thruster in self.sat.thrusters:
            T = thruster.thrust_max * np.dot(thruster.direction, direction) # Force disponnible dans l'axe voulu
            if T != 0:  # Évite la division par 0
                pow = power / T
                if pow <= 20:   # Si le nombre d'itération n'excède pas les 20 (pour se rapprocher de l'instantané)
                    n = ceil(pow)
                    return {'power': pow / n, 'n': n, 'thruster': thruster.name}
        # Si aucun propulseur ne convient, on ne peux pas réaliser la manoeuvre
        return None

    def power_for_rotation(self, period, axe=2):
        """
        Retourne la puissance (de 0% à 100%) à appliquer au thruster précisé en sortie, durant niteration de dt sec,
        afin de tourner avec la période souhaité autour de l'axe désiré.

        :param period: Durée de la révolution du satellite (en sec).
                       Note: Pour une roration sens horaire, mettre une période négative pour changer de signe.

        :type period: float
        :param axe: Indice de l'axe de rotation
        :type axe: int   (0, 1 ou 2)
        :return: - power : Puissance de 0% à 100% du thruster,
                 - n : Nombre d'itération nécessaire à l'accélération,
                 - thruster : Nom du thruster à activer.
        :rtype : dict[float]
        """
        # Coefficient nécéssaire pour le choix du thruster (vérifier sa  direction)
        power = 2*np.pi * self.sat.inertia[axe] / (period * self.simulator.dt)
        if power == 0:
            return {'power': 0, 'n': 1, 'thruster': 'main'}  # Instructions inutiles, pour ne pas faire crash le sat
        # Essaie de tous les propulseurs :
        for thruster in self.sat.thrusters:
            T = thruster.torque_max[axe]  # Couple disponnible dans l'axe voulu
            if T != 0:  # Évite la division par 0
                if sign(power) == sign(T):
                    power /= thruster.torque_max[axe]
                    n = ceil(power)
                    return {'power': power / n, 'n': n, 'thruster': thruster.name}
        # Si aucun propulseur ne convient, on ne peux pas réaliser la manoeuvre
        return None

    def update(self, infos=True):
        """
        Envoie les commandes au satellite selon les instructions demandés par l'utilisateur. Vérifie une à une les
        différentes instructions possibles, et les mets à jours si besoin.

        :param infos: Indique si les informations doivent être affichées (par défaut True).
        :type infos: boolean
        """
        # Change le statut du satellite une fois décollé
        if self.sat.islanded or self.sat.istakingoff:
            if self.sat.get_radius() > 1.01 * self.sat.planet_ref.radius:
                self.sat.islanded, self.sat.istakingoff = False, False

        # Instruction : Rejoindre l'orbite géo au rayon demandée
        if not self.reach_geo is None:
            # Phase d'approche :
            if self.reach_geo['step'] == 'approach':    # Phase 1
                # Thrust nécéssaire à maintenir   acc = gamma_1 * Poids_sat * ur
                T = (self.reach_geo['gamma_1'] + 1) * np.linalg.norm(self.sat.ag) * self.sat.mass
                # Activation du propulseur principal :
                self.sat.get('main').on(power=T / self.sat.get('main').thrust_max)
                # Si la manoeuvre passe en phase 2 (selon la distance)
                if self.sat.get_radius() / self.reach_geo['radius'] >= self.reach_geo['switch_step']:
                    self.reach_geo['step'] = 'reaching'     # Etape suivante : Phase 2
                    self.sat.get('left').on(power=self.reach_geo['rot_pulse'])  # Mise en rotation (une seul itération)
                    print(f"   | ctr: phase 2 of geo reaching started")
            elif self.reach_geo['step'] == 'reaching':  # Phase 2
                self.sat.get('left').off()  # Arrêt de la rotation (une seul itéartion)
                # Calcul de l'angle entre le vecteur directeur du satellite et ur :
                angle = np.arccos(np.dot(normalize(self.sat.x - self.planet.x)[0], self.sat.ux[0]))
                # Thrust nécéssaire à maintenir   acc = gamma_2 * Poids_sat * ur   +   acc_utheta
                # Tiens compte de l'effet d'interie (force centrifuge)
                T = (self.reach_geo['gamma_2'] + 1) * np.linalg.norm(self.sat.ag)
                T -= self.sat.get_speed() ** 2 / self.sat.get_radius() * np.sin(angle) ** 2
                T *= self.sat.mass / np.cos(angle)
                # Activation du propulseur principal :
                self.sat.get('main').on(power=T / self.sat.get('main').thrust_max)
                # Vérification si le satellite est suffisement proche de l'orbite GEO désirée
                epsilon = self.reach_geo['epsilon']['radius']
                if 1 - epsilon < self.sat.get_radius() / self.reach_geo['radius'] < 1 + epsilon:
                    epsilon = self.reach_geo['epsilon']['speed']
                    if 1 - epsilon < self.sat.get_speed() / self.reach_geo['speed'] < 1 + epsilon:
                        epsilon = self.reach_geo['epsilon']['angle']
                        if 1 - epsilon < angle/ (np.pi / 2) < 1 + epsilon:
                            # Si le rayon, la vitesse et la direction sont suffisement proches de ceux désirés (1% max),
                            # la position / vitesse du satellite sont manuellement corrigées, pour éviter une divergence
                            ur = normalize(self.sat.x)
                            self.sat.x = ur * self.reach_geo['radius']
                            self.sat.v = np.cross(-ur, self.z) * self.reach_geo['speed']
                            # On arrête toute ommande
                            self.sat.get('main').off()
                            print(f"   | ctr: geo reached (forced)     ({self.simulator.time} sec)")
                            self.reach_geo = None
                            # Ordonne au satellite de synchroniser sa rotation, pour toute manoeuvre future :
                            self.reach_sync = self.sat.controls['ctr-run-synchronize'] = [((0, {}))]

        # Instruction : Synchroniser la rotation avec la période orbitale
        elif not self.reach_sync is None:
            # Phase 1 : Arrêt de rotation
            if self.reach_sync['step'] == 'stop':
                # Si le nombre d'itération nécéssaire à la rotation a été atteint, on arrête le propulseur
                if self.reach_sync['iteration'] == self.reach_sync['n']:
                    self.sat.get(self.reach_sync['thruster']).off()
                    # Passage en Phase 2 : Attente d'avoir le bon angle (perpendiculaire au sol) à 0.5% prés
                    self.reach_sync = {'step': 'wait', 'epsilon': 0.005, 'period': self.get_period()}
                    #print(f"   | ctr: wait to synchronize rotation   ({self.simulator.time} sec)")
                else:
                # Sinon, on passe à l'itération suivante
                    self.reach_sync['iteration'] += 1
            # Phase 2 : Attente du bon angle (perpendiculaire au sol)
            if self.reach_sync['step'] == 'wait':
                # Angle entre ur et -uy (plus précisement, son cosinus, qui nous suffit à vérifier l'alignement)
                cos_ang = np.dot(normalize(self.sat.x - self.planet.x), -self.sat.uy)
                if cos_ang > 1 - self.reach_sync['epsilon']:
                    # Si on est suffismeent alligné, on allume le propulseur nécéssaire à la rotation
                    self.reach_sync = self.power_for_rotation(period=self.reach_sync['period'])
                    self.sat.get(self.reach_sync['thruster']).on(power=self.reach_sync['power'])
                    # Passage à la Phase 3 : Synchronisation
                    self.reach_sync['step'], self.reach_sync['iteration'] = 'sync', 0
            # Phase 3 : Synchronisation de la rotation
            if self.reach_sync['step'] == 'sync':
                # Si le nombre d'itération nécéssaire à la rotation a été atteint, on arrête le propulseur
                if self.reach_sync['iteration'] == self.reach_sync['n']:
                    self.sat.get(self.reach_sync['thruster']).off()
                    print(f"   | ctr: finish to synchronize rotation   ({self.simulator.time} sec)")
                    self.reach_sync = None
                else:
                # Sinon, on passe à l'itération suivante
                    self.reach_sync['iteration'] += 1

        # Instruction : Réaliser un transfert d'Hohmann
        elif not self.do_homhann is None:
            # Phase 1 : Quitter la GEO initiale pour rejoindre l'elliptique
            if self.do_homhann['step'] == 'reach_elliptic':
                # Données de mise en rotation :
                if self.do_homhann.get('rot'):
                    if self.do_homhann['rot']['n'] == self.do_homhann['iteration']:
                        self.sat.get(self.do_homhann['rot']['thruster']).off()
                # Si les itérations d'accélération/freinage sont atteints:
                if self.do_homhann['n'] == self.do_homhann['iteration']:
                    # Passage en Phase 2
                    self.do_homhann['step'] = 'on_elliptic'
                    print(f"   | ctr: elliptical orbit reached   ({self.simulator.time} sec)")
                    self.sat.get(self.do_homhann['thruster']).off()
                else:
                # Sinon, on passe à l'itération suivante
                    self.do_homhann['iteration'] += 1
            # Phase 2 : Attendre de parcourir la demi-orbite elliptique ...
            # ... Durant cette phase, mise en rotation pour arriver aligné à l'apogée/périgée
            # Si on dépasse le time de 'stop-at' (heure d'arrivée prévue à la demi-orbite) :
            if self.do_homhann['step'] == 'on_elliptic' and self.simulator.time >= self.do_homhann['stop_at']:
                r = self.do_homhann['radius']
                dv = self.geo_speed(radius=r) - self.sat.get_speed()
                # Calcul de la pusisance nécéssaire au changement vers l'orbite GEO finale
                self.do_homhann = self.power_for_speed(speed=dv)
                if self.do_homhann is None:
                    print(f'   | ctr: impossible to reach second GEO   ({self.simulator.time} sec)')
                    return None # Quitte le programme
                else:
                    # Si le changement est possible, allumage du propulseur nécessaire :
                    self.do_homhann['radius'] = r
                    self.sat.get(self.do_homhann['thruster']).on(power=self.do_homhann['power'])
                    # Passage à la Phase 3
                    self.do_homhann['step'], self.do_homhann['iteration'] = 'reach_geo', 0
            # Phase 3 : Rejoindre l'orbite GEO d'arrivée
            if self.do_homhann['step'] == 'reach_geo':
                if self.do_homhann['iteration'] == self.do_homhann['n']:
                    self.sat.get(self.do_homhann['thruster']).off()
                    # Si le rayon, la vitesse et la direction sont suffisement proches de ceux désirés (1% max),
                    # la position / vitesse du satellite sont manuellement corrigées, pour éviter une divergence
                    ur = normalize(self.sat.x - self.planet.x)
                    self.sat.x = self.do_homhann['radius'] * ur
                    self.sat.v = self.geo_speed(radius=self.do_homhann['radius']) * np.cross(-ur, self.z)
                    # On arrête toute ommande
                    print(f"   | ctr: successful Homhann transfer     ({self.simulator.time} sec)")
                    self.do_homhann = None
                    # Ordonne au satellite de synchroniser sa rotation, pour toute manoeuvre future :
                    self.reach_sync = self.sat.controls['ctr-run-synchronize'] = [((0, {}))]
                else:
                    self.do_homhann['iteration'] += 1
