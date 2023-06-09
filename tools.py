import numpy as np
from math import acos, asin, atan2


def euler(f, df, ddf, dt):
    df = df + dt * ddf
    f = f + dt * df
    return f, df, ddf


def RK4(f, df, dt):
    # A développer
    return f, df
