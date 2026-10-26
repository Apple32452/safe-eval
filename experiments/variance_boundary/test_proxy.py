import unittest

import numpy as np

from audit_proxy import within_row_proxy


class ProxyFormulaTests(unittest.TestCase):
    def test_closed_form_matches_brute_grid(self):
        a = np.array([[1., 9., 4.], [4., 1., 9.]])
        q = np.array([[.1, .1, .1], [.7/3, .7/3, .7/3]])
        uniform, optimum = within_row_proxy(a, q)
        self.assertAlmostEqual(optimum, (1+3+2)**2/.3 + (2+1+3)**2/.7)
        self.assertGreater(uniform, optimum)
        for i in range(1, 20):
            for j in range(1, 20-i):
                first = .3*np.array([i, j, 20-i-j])/20
                # Keep the second row at its optimum.
                second = .7*np.sqrt(a[1])/np.sqrt(a[1]).sum()
                candidate = np.vstack((first, second))
                self.assertGreaterEqual(float(np.sum(a/candidate)), optimum-1e-10)

    def test_equal_proxy_weights_have_no_within_row_gain(self):
        a = np.array([[2., 2., 2.], [4., 4., 4.]])
        q = np.array([[.1, .1, .1], [.7/3, .7/3, .7/3]])
        uniform, optimum = within_row_proxy(a, q)
        self.assertAlmostEqual(uniform, optimum)


if __name__ == '__main__':
    unittest.main()
