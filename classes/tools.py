import numpy as np
from math import acos, asin, atan2, pi


def euler(f, df, ddf, dt):
    df = df + dt * ddf
    f = f + dt * df
    return f, df, ddf


def RK4(f, df, dt):
    # A développer
    return f, df


def normalize(vec):
    return vec / np.linalg.norm(vec)


def rotation_matrix(angle, axe='z'):
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
    return np.dot(np.array(base).T, np.array(point)) + np.array(base_center)


def errors(u, v, normalize=True):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu * nv == 0:
        if normalize:
            return 1, 1
        else:
            return 100, 100
    else:
        err_norm, err_ang = np.abs(nv - nu) / nv, np.arccos(np.dot(u, v) / (nu * nv)) / pi
        if normalize:
            return err_norm, err_ang
        else:
            return round(100 * err_norm, 1), round(100 * err_ang, 1)


def zero(size=3):
    return np.array([0] * size)


def sign(inp):
    return int(inp / np.abs(inp))
