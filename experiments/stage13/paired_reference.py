"""Slow independent integer/Fraction checks, separate from optimized inference."""
from __future__ import annotations

from fractions import Fraction
import math


def brute_raw(n, positive, negative, equal, quantum, cap):
    t = positive + negative + equal
    output = []
    for a, b in ((positive, negative), (negative, positive)):
        if a <= b:
            output.append(0)
            continue
        products = []
        for total_a in range(a, n + 1):
            for total_b in range(max(total_a, b), n - total_a + 1):
                total_c = n - total_a - total_b
                if total_c >= equal:
                    products.append(math.comb(total_a, a) * math.comb(total_b, b) * math.comb(total_c, equal))
        if not products:
            output.append(cap)
        else:
            ratio = Fraction(2 * math.comb(n, t), (t + 1) * (t + 2) * max(products))
            output.append(min(cap, int(quantum * ratio)))
    return output


def rational_factors(z, lower, upper, n, prediction_scale):
    value = Fraction(int(z), n * prediction_scale)
    limits = (Fraction(int(lower), n * prediction_scale),
              Fraction(int(upper), n * prediction_scale))
    result = []
    for direction in (1, -1):
        low = limits[0] if direction == 1 else -limits[1]
        factors = []
        for expert in range(8):
            stake = Fraction(2 ** expert, 8)
            if low < 0:
                stake = min(stake, -Fraction(1, 2) / low)
            factors.append(1 + direction * stake * value)
        result.append(factors)
    return result


def raw_at_modes(n, a, b, c, quantum, cap):
    """Independent scalar neighbor search, exact products; avoids binomial tables."""
    if a <= b:
        return 0
    products = []
    for d in (0, 1):
        left, right = max(a, b - d), (n - c - d) // 2
        if left > right:
            continue
        # Start near the continuous count ratio, then check exact neighbors.
        t = a + b + c
        k = min(right, max(left, round(n * (a + b) / max(2 * t, 1) - d / 2)))
        def product(j):
            return math.comb(j, a) * math.comb(j + d, b) * math.comb(n - 2 * j - d, c)
        value = product(k)
        while k > left:
            previous = product(k - 1)
            if previous <= value:
                break
            k -= 1
            value = previous
        while k < right:
            following = product(k + 1)
            if following <= value:
                break
            k += 1
            value = following
        products.append(value)
    if not products:
        return cap
    return min(cap, 2 * quantum * math.comb(n, a + b + c) //
               ((a + b + c + 1) * (a + b + c + 2) * max(products)))
