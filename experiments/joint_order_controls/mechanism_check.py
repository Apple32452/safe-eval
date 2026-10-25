"""Verify the stated conditional log-growth examples against analytic KL."""
import argparse
import json
from pathlib import Path

import numpy as np

from controls import rebalance
from joint_order import (DIRECTED, IMPLIED, JOINT_NULLS, ORDERS, PAIR_NULLS,
                         event_rows, fitted_factor)


def bernoulli_kl(p, r):
    return p*np.log(p/r)+(1-p)*np.log((1-p)/(1-r))


def one(p, order, projected):
    p, projected = np.array(p), np.array(projected)
    q = np.full(3, 1/3)
    s, m = np.zeros(3, int), np.full(3, 16)
    a = np.column_stack((q*(1-p), q*p)).ravel()
    idx = ORDERS.index(order)
    null = JOINT_NULLS[idx]
    joint = fitted_factor(event_rows(null.vertices(s, m), s, m, q), q, p)[0]
    factors = np.array([fitted_factor(event_rows(PAIR_NULLS[i].vertices(s, m),
                                                 s, m, q), q, p)[0]
                        for i in IMPLIED[idx]])
    combined = rebalance(factors, a)[0]
    joint_growth = float(a @ np.log(joint))
    analytic = float(q @ bernoulli_kl(p, projected))
    np.testing.assert_allclose(joint_growth, analytic, atol=2e-7)
    pair_growth = np.log(factors) @ a
    return {'prior': p.tolist(), 'weak_order': list(order),
            'projected_marginals': projected.tolist(),
            'joint_expected_log_factor': joint_growth,
            'analytic_kl': analytic,
            'largest_implied_pair_log_factor': float(pair_growth.max()),
            'rebalanced_pair_log_factor': float(a @ np.log(combined)),
            'pair_log_factors': {str(DIRECTED[i]): float(g)
                                 for i, g in zip(IMPLIED[idx], pair_growth)}}


def run():
    a = one((.2, .5, .8), (1, 0, 2), (.35, .35, .8))
    b = one((.2, .5, .8), (0, 2, 1), (.2, .65, .65))
    c = one((.1, .2, .9), (2, 1, 0), (.4, .4, .4))
    for row in (a, b):
        np.testing.assert_allclose(row['joint_expected_log_factor'],
                                   row['largest_implied_pair_log_factor'], atol=2e-7)
        np.testing.assert_allclose(row['joint_expected_log_factor'],
                                   row['rebalanced_pair_log_factor'], atol=2e-7)
    assert c['joint_expected_log_factor'] > c['largest_implied_pair_log_factor']+1e-6
    return {'status': 'passed', 'units': 'predicted log evidence per purchased cell',
            'stopping_cost_theorem': False, 'examples': [a, b, c]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
