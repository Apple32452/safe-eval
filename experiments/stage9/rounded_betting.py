"""Conservative binary64 lower bounds for predictable betting capital.

Arithmetic assumptions: IEEE-754 binary64 round-to-nearest for +,-,*,/,
nextafter/frexp/ldexp, and a sum of nonnegative numbers using at most N-1
additions. No logarithms of prediction wealth are used. The predictor and
variance heuristic may be arbitrary predictable finite float values.
"""
from fractions import Fraction
import math
import numpy as np


def down(x):
    return np.nextafter(np.asarray(x, dtype=np.float64), -np.inf)


def up(x):
    return np.nextafter(np.asarray(x, dtype=np.float64), np.inf)


def upper_fraction(value):
    value = Fraction(value)
    result = float(value)
    return math.nextafter(result, math.inf) if Fraction.from_float(result) < value else result


def ratio_bounds(numerator, n):
    numerator = np.asarray(numerator)
    x = numerator / n
    return (np.where(numerator == 0, 0., np.where(numerator == n, 1., down(x))),
            np.where(numerator == 0, 0., np.where(numerator == n, 1., up(x))))


def prediction_bounds(successes, unseen, mu, indices, y):
    trials, n = mu.shape
    r = unseen.sum(axis=1)
    summed = np.sum(np.where(unseen, mu, 0.), axis=1)
    unit = Fraction(1, 2**53)
    gamma = upper_fraction((n-1)*unit / (1-(n-1)*unit))
    sum_lo = np.maximum(0., down(summed / up(1 + gamma)))
    sum_hi = up(summed / down(1 - gamma))
    base_lo = down(down(successes + sum_lo) / n)
    base_hi = up(up(successes + sum_hi) / n)
    rlo, rhi = ratio_bounds(r, n)
    max_mu = np.max(np.where(unseen, mu, -np.inf), axis=1)
    min_mu = np.min(np.where(unseen, mu, np.inf), axis=1)
    support_lo = down(base_lo - up(rhi * max_mu))
    support_hi = up(base_hi + up(rhi * up(1 - min_mu)))
    center_base = (successes + summed) / n
    if y is None:
        return support_lo, support_hi, center_base
    chosen = mu[np.arange(trials), indices]
    residual_lo, residual_hi = down(y - chosen), up(y - chosen)
    correction_lo = down(np.where(residual_lo < 0, rhi, rlo) * residual_lo)
    correction_hi = up(np.where(residual_hi < 0, rlo, rhi) * residual_hi)
    zlo, zhi = down(base_lo + correction_lo), up(base_hi + correction_hi)
    return zlo, zhi


def stakes(support_lo, support_hi, qlo, qhi, eta):
    positive_distance = up(qhi[None, :] - support_lo[:, None])
    negative_distance = up(support_hi[:, None] - qlo[None, :])
    with np.errstate(over="ignore", divide="ignore"):
        pcap = np.where(positive_distance > 0, down(.9 / positive_distance), np.inf)
        mcap = np.where(negative_distance > 0, down(.9 / negative_distance), np.inf)
    return np.minimum(eta[:, None], pcap), np.minimum(eta[:, None], mcap)


def lower_factors(zlo, zhi, qlo, qhi, positive, negative):
    fp = down(1 + down(positive * down(zlo[:, None] - qhi[None, :])))
    fm = down(1 - up(negative * up(zhi[:, None] - qlo[None, :])))
    if np.any(~np.isfinite(fp)) or np.any(~np.isfinite(fm)) or min(fp.min(), fm.min()) <= 0:
        raise ValueError("Positive conservative factor bounds required")
    return fp, fm


class ScaledCapital:
    def __init__(self, shape):
        self.m = np.full(shape, .5, dtype=np.float64)
        self.e = np.ones(shape, dtype=np.int32)

    def update(self, factor):
        product = down(self.m * factor)
        if np.any(product <= 0) or not np.isfinite(product).all():
            raise ValueError("Scaled product left its safe range")
        self.m, exponent = np.frexp(product)
        self.e += exponent


def average_crossed(positive, negative, alpha):
    if alpha <= 0:
        return np.zeros(positive.m.shape, dtype=bool)
    threshold = upper_fraction(1 / Fraction(alpha))
    hm, he = math.frexp(threshold)
    common = np.maximum(positive.e, negative.e)
    with np.errstate(under="ignore"):
        pm = np.maximum(0., down(np.ldexp(positive.m, positive.e - common)))
        mm = np.maximum(0., down(np.ldexp(negative.m, negative.e - common)))
    average = np.maximum(0., down(pm + mm)) * .5
    mantissa, exponent = np.frexp(average)
    exponent += common
    return (exponent > he) | ((exponent == he) & (mantissa >= hm))
