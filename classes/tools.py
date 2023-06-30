import numpy as np
from math import acos, asin, atan2, pi


def euler(f, df, ddf, dt):
    """
    Effectue l'intégration numérique d'une fonction à l'aide de la méthode d'Euler.

    :param f: Valeur de la fonction à intégrer.
    :type f: float or 1D-array
    :param df: Valeur de la dérivée de la fonction.
    :type df: float or 1D-array
    :param ddf: Valeur de la dérivée seconde de la fonction.
    :type ddf: float or 1D-array
    :param dt: Pas de temps (en sec)
    :type dt: float
    :return: Résultat de l'intégration numérique.
    :rtype: float or 1D-array
    """
    df = df + dt * ddf
    f = f + dt * df
    return f, df, ddf


def normalize(vec):
    """
    Normalise le vecteur, sans changer la direction

    :param vec: Vecteur non normalisé
    :type vec: 1D-array
    :return: Vecteur normalisé, de même direction
    :rtype: 1D-array
    """
    return vec / np.linalg.norm(vec)


def rotation_matrix(angle, axe='z'):
    """
    Calcul la matrice de rotation, d'un angle désiré autour de l'axe voulu

    :param angle: Angle de rotation (en rad, sens trigonométrique)
    :type angle: float
    :param axe: Nom de l'axe de rotation
    :type axe: string   ('x', 'y' or 'z')
    :return: Matrice 3*3 de rotation
    :rtype: 2D-array   (3*3 components)
    """
    if axe in [2, 'z']:
        return np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    elif axe in [1, 'y']:
        return np.array([[np.cos(angle), 0, np.sin(angle)], [0, 1, 0], [-np.sin(angle), 0, np.cos(angle)]])
    elif axe in [0, 'x']:
        return np.array([[1, 0, 0], [0, np.cos(angle), -np.sin(angle)], [0, np.sin(angle), np.cos(angle)]])
    else:
        print(f" /!\\ Aucun axe de rotation trouvé ")
        return np.eye(3)


def from_other_base(point, base, base_center=(0, 0, 0)):
    """
    Calcul les composantes d'un vetceur dans une autre base, composée de 3 vecteurs orthonormées

    :param point: Coordonnées du vecteur à modifier
    :type point: 1D-array   (3 components)
    :param base: Matrice de changement de base (composé des 3 vetceurs orthonormées de la nouvelle base)
    :type base: 2D-array   (3*3 components)
    :param base_center: Coordonnées du centre de la nouvelle base
    :type base_center: 1D-array   (3 components)
    :return: Coordonnées du vecteur dans la nouvelle base
    :rtype: 1D-array   (3 components)
    """
    return np.dot(np.array(base).T, np.array(point)) + np.array(base_center)


def zero(size=3):
    """
    Retourne le vecteur nul, sous numpy

    :param size: Taille du vecteur (par défaut 3).
    :type size: int
    :return: Vecteur nul de taille size
    :rtype: 1D-array
    """
    return np.array([0] * size)


def sign(inp):
    """
    Retourne le signe de la valeur en entrée

    :param inp: Valeur positive ou négative
    :type inp: float
    :return: Coefficients -1 ou +1, selon le signe
    :rtype: signed int   (-1 or 1)
    """
    return int(inp / np.abs(inp))
