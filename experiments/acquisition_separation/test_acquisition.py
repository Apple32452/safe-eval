import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from optimal_acquisition import (KINDS, PRIORS, Model, dual_bound, solve,
                                 zero_error_optimum, evaluate_policy)


class ExactAcquisitionChecks(unittest.TestCase):
    def test_fixed_world_branches_and_unique_purchase_cost(self):
        for kind in KINDS:
            model = Model(n=1, kind=kind)
            for s,actions in enumerate(model.actions):
                parent = model.states[s][0]
                for action in actions:
                    if not action.children: continue
                    for child,_ in action.children:
                        after = model.states[child][0]
                        self.assertTrue(all(x == -1 or x == y for x,y in zip(parent,after)))
                        self.assertEqual(sum(x != -1 for x in after)-sum(x != -1 for x in parent), action.cost)
                        self.assertGreater(child,s)
                    for w in model.compatible[s]:
                        self.assertEqual(sum((p for child,p in action.children
                                              if w in model.compatible[child]), F(0)), 1)

    def test_one_item_zero_error_requires_every_cell(self):
        for kind in KINDS:
            model = Model(n=1, graph='triangle', kind=kind)
            value,policy = zero_error_optimum(model,model.probabilities('opposed'))
            costs,errors,_ = evaluate_policy(model,policy)
            self.assertEqual(value,3)
            self.assertEqual(set(costs),{F(3)})
            self.assertEqual(set(errors),{F(0)})

    def test_risk_bound_holds_for_each_world_under_misspecified_prior(self):
        for kind in KINDS:
            record = solve(Model(n=1,graph='star',kind=kind), 'one_hot', F(1,20))
            self.assertLessEqual(max(map(F,record['world_errors'])),F(1,20))
            self.assertEqual(len(record['world_errors']),8)
            self.assertLessEqual(F(record['lower']),F(record['upper']))
            self.assertLess(float(F(record['certified_gap'])),1e-6)

    def test_prior_full_support_and_cell_row_symmetry(self):
        for name in PRIORS:
            p=Model().probabilities(name)
            self.assertEqual(sum(p),1)
            self.assertGreater(min(p),0)
        model=Model(); p=model.probabilities('independent')
        for i,w in enumerate(model.worlds):
            for row in range(3):
                permuted=list(w)
                permuted[2*row],permuted[2*row+1]=permuted[2*row+1],permuted[2*row]
                self.assertEqual(p[i],p[model.worlds.index(tuple(permuted))])

    def test_dual_bound_checks_all_actions_not_only_policy_actions(self):
        model=Model(n=1,kind='common_retirement')
        p=model.probabilities('monotone'); mass=model.masses(p)
        penalties=tuple(F(i+1,3) for i in range(8))
        lower,value=dual_bound(model,p,F(1,20),penalties)
        self.assertLessEqual(lower,3)
        for s,actions in enumerate(model.actions):
            for action in actions:
                if action.answer is None:
                    rhs=mass[s]*action.cost+sum((q*value[c] for c,q in action.children),F(0))
                else:
                    rhs=sum((penalties[w] for w in model.compatible[s]
                             if model.truth[w]!=action.answer),F(0))
                self.assertLessEqual(value[s],rhs)


if __name__=='__main__': unittest.main()
