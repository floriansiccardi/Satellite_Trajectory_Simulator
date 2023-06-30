# MGA802_Projet
Simulateur Orbital
==================

Ce projet consiste en un **simulateur orbital** permettant de représenter le trajet d'un satellite en 3 dimensions. 
Le satellite est modélisé comme un parallélépipède rectangle avec 4 propulseurs : 
- un propulseur principal pour le décollage
- un à gauche et un à droite pour l'orientation,  
- un au-dessus pour le freinage. 
La puissance des propulseurs dépendra du poids du satellite.

Fonctionnalités
---------------

Le simulateur offre les fonctionnalités suivantes :

1. Décollage automatique du satellite depuis la surface de la terre.
2. Trajet automatique vers une première orbite géostationnaire.
3. Changement d'orbite géostationnaire vers une seconde orbite géostationnaire.
4. Configuration flexible du satellite :
   - Rayon de l'orbite géostationnaire initiale et finale (la modification de l'orbite initiale n'est pas conseillée).
   - Poids et dimensions du satellite.
   - Temps de changement d'orbite
   - Temps de simulation et pas de simulation.
5. Génération de 5 figures en sortie :
   - Simulation de la trajectoire du satellite en fonction du temps de simulation.
   - Figure 3D représentant la trajectoire suivie et les cercles des deux orbites géostationnaires demandées.
   - Graphes montrant l'évolution de la puissance des propulseurs, du rayon et de la vitesse en fonction du temps.

Installation
------------

Pour installer les librairies nécessaires, exécutez la commande suivante :
```pip install -r requirements.txt```.

Utilisation
-----------

1. Modifiez les paramètres du satellite et du trajet dans le fichier `donnees.yaml`.
2. Lancez la simulation en exécutant le fichier `main.py`.

Gestion des erreurs
-------------------

Le programme vérifie la cohérence des données entrées par l'utilisateur. 
En cas de données non cohérentes, des erreurs simples seront affichées, 
permettant à l'utilisateur de localiser et corriger le problème.

Si le satellite entre en collision avec un élément de la simulation, 
un message d'erreur sera également affiché.

Fichier DEMO.py
---------------

Le fichier `DEMO.py` fournit un exemple de décollage du satellite jusqu'à une 
orbite géostationnaire de 9.10^6 m de rayon, suivi d'un changement vers une orbite géostationnaire 
de 12.10^6 m pour un satellite de 1000 kg et de dimensions 3 m sur 1 m sur 1 m et un pas de simulation de 5.

Documentation
-------------

La documentation générée avec Sphinx est disponible dans le dossier `MGA802_Projet\docs\build\html`. 
Vous pouvez accéder à la documentation en ouvrant le fichier `index.html`

Licence
-------

Ce projet est sous licence **Creative Commons Attribution - Pas d'Utilisation Commerciale - Partage dans les Mêmes Conditions Conditions 4.0 International** (CC BY-NC-SA 4.0).

Cela signifie que vous êtes libre de :

- **Partager** 
- **Adapter** 

Selon les conditions suivantes :

- **Attribution** 
- **Pas d'Utilisation Commerciale** 
- **Partage dans les Mêmes Conditions** 

Pour plus d'informations sur cette licence, veuillez consulter le fichier `LICENSE.md`.

Bonne simulation !
------------------

