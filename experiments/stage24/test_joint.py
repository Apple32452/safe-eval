from fractions import Fraction as F
from itertools import product, permutations
import unittest
import numpy as np
from joint import factor_integers, conservative_update, run, grid, project


class JointChecks(unittest.TestCase):
    def test_exact_conditional_factor_expectation_and_rounding(self):
        rng = np.random.default_rng(72)
        probes = 0
        for m in (2, 3, 4):
            for n in (3, 5, 8):
                for _ in range(20):
                    x = rng.integers(0, 2, (n, m)); t = int(rng.integers(n))
                    sums, k = x[:t].sum(axis=0), x.sum(axis=0)
                    weights = rng.integers(1, 10, n-t)
                    for d in product((-1, 0, 1), repeat=m):
                        expectation = F(0)
                        for i, y in enumerate(x[t:]):
                            num, den = factor_integers(k[None, :], sums, np.array([d]), weights, weights[i], y)
                            f = F(int(num[0]), int(den[0])); self.assertGreaterEqual(f, F(1, 2))
                            expectation += F(int(weights[i]), int(weights.sum()))*f
                            low = conservative_update(np.array([1.]), num, den)[0]
                            self.assertLessEqual(F(float(low)), f)
                        self.assertEqual(expectation, 1); probes += 1
        self.assertEqual(probes, 7020)

    def test_general_partial_cell_unbiasedness(self):
        # Arbitrary cross-system correlation and unequal adaptive probabilities.
        x = [[F(1), F(0), F(1)], [F(0), F(1), F(1)]]
        observed = {(0, 0), (1, 2)}; cells = [(v, i) for v in range(2) for i in range(3) if (v, i) not in observed]
        weights = (1, 4, 2, 3); sums = [sum(x[v][i] for vv, i in observed if vv==v) for v in range(2)]
        expectation = [F(0), F(0)]
        for (v, i), w in zip(cells, weights):
            p = F(w, sum(weights)); z = [s/F(3) for s in sums]; z[v] += x[v][i]/(3*p)
            for j in range(2): expectation[j] += p*z[j]
        self.assertEqual(expectation, [sum(row)/3 for row in x])

    def test_ignoring_propensities_is_biased(self):
        # Uniform formula on a draw biased toward the one: E Z=.75 rather than .5.
        self.assertEqual(F(1, 4)*0+F(3, 4)*1, F(3, 4))
        self.assertNotEqual(F(3, 4), F(1, 2))

    def test_exhaustive_adaptive_binary_coverage(self):
        n, m = 3, 2; edges = np.array([[0, 1]])
        for bits in product((0, 1), repeat=n*m):
            x = np.array(bits).reshape(n, m); truth = np.sign(x[:, 0].sum()-x[:, 1].sum())
            for covariance in (False, True):
                failure, mass = F(0), F(0)
                for path in permutations(range(n)):
                    observed, remaining, uniforms, probability = [], list(range(n)), [], F(1)
                    from joint import row_weights
                    history = np.array([[.1, .9], [.7, .2], [.8, .8]])
                    for item in path:
                        w = row_weights(history, observed, remaining, True); j = remaining.index(item)
                        uniforms.append(float(F(int(w[:j].sum()), int(w.sum()))+F(int(w[j]), 2*int(w.sum()))))
                        probability *= F(int(w[j]), int(w.sum()))
                        remaining.pop(j); observed.append(x[item])
                    r = run(n, m, lambda i: x[i], history, uniforms, edges, covariance, True)
                    index = int(np.ravel_multi_index(tuple(x.sum(axis=0)), (n+1,)*m))
                    covered = np.unpackbits(r['masks'], axis=1)[:, index].all()
                    if not covered: failure += probability
                    mass += probability
                    self.assertEqual(len(r['queried']), len(set(r['queried'])))
                    self.assertEqual(int(r['decisions'][0]), int(truth))
                self.assertEqual(mass, 1); self.assertLessEqual(failure, F(1, 20))

    def test_predictability_and_reproduction(self):
        n, m = 5, 2; rng = np.random.default_rng(19); x = rng.integers(0, 2, (n, m))
        history = rng.random((n, m)); uniforms = rng.random(n); edges = np.array([[0, 1]])
        snapshots = []
        for flip in (False, True):
            state = []
            def hook(t, item, values):
                if t==0: state.append(values)
            r = run(n, m, lambda i: 1-x[i] if flip else x[i], history, uniforms, edges, True, True, hook)
            snapshots.append(state[0])
        for k in ('weights', 'direction', 'sums'): np.testing.assert_array_equal(snapshots[0][k], snapshots[1][k])
        a = run(n, m, lambda i: x[i], history, uniforms, edges, True, True)
        b = run(n, m, lambda i: x[i], history, uniforms, edges, True, True)
        for key in a: np.testing.assert_array_equal(a[key], b[key])

    def test_empty_set_never_certifies_signs(self):
        np.testing.assert_array_equal(project(np.zeros((0, 2)), [[0, 1]]), [2])


if __name__ == '__main__': unittest.main()
