from fractions import Fraction as F
from itertools import product, permutations
import unittest
import numpy as np
from partial import ppr, run


class PartialChecks(unittest.TestCase):
    def test_all_scalar_null_conditional_expectations(self):
        for n in range(1,9):
            for k in range(n+1):
                for t in range(n):
                    for s in range(t+1):
                        if not s<=k<=s+n-t:continue
                        p = F(k-s,n-t);q=F(s+1,t+2);expectation=F(0)
                        for y,prob in ((0,1-p),(1,p)):
                            if prob:
                                factor = (q if y else 1-q)/prob
                                self.assertEqual(ppr(n,t+1,s+y,k), ppr(n,t,s,k)*factor)
                                expectation += prob*factor
                        self.assertLessEqual(expectation,1)

    def test_boundary_is_supermartingale_not_martingale(self):
        self.assertEqual(ppr(4,1,0,0),F(1,2))

    def test_exhaustive_adaptive_cell_coverage(self):
        n,m=2,2;edges=np.array([[0,1]])
        for bits in product((0,1),repeat=n*m):
            x=np.array(bits).reshape(m,n);idx=int(np.ravel_multi_index(tuple(x.sum(axis=1)),(n+1,)*m))
            for mode in ('hedge','product','mixture','peak'):
                bad=F(0)
                for paths in product(list(permutations(range(n))),repeat=m):
                    us=np.zeros((m,n))
                    for v,path in enumerate(paths):
                        left=list(range(n))
                        for t,item in enumerate(path):
                            j=left.index(item);us[v,t]=(j+.5)/len(left);left.pop(j)
                    r=run(n,m,lambda v,i:x[v,i],edges,us,mode)
                    if not np.unpackbits(r['masks'],axis=1)[:,idx].all():bad+=F(1,4)
                    np.testing.assert_array_equal(r['decisions'],np.sign(x.sum(axis=1)[0]-x.sum(axis=1)[1]))
                self.assertLessEqual(bad,F(1,20))

    def test_strict_separation_and_existing_control_match(self):
        import sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'stage24'))
        from baselines import stage22
        for n in (4,6,8):
            x=np.zeros((n,3),dtype=int);x[:,0]=1;edges=np.array([[0,1],[0,2]])
            baseline=stage22(x,edges,np.arange(n,dtype=np.int32),np.tile(np.arange(3),(n,1)))['completion_cost']
            for mode in ('hedge','product','mixture','peak'):
                r=run(n,3,lambda v,i:x[i,v],edges,np.full((3,n),.5),mode)
                self.assertLessEqual(r['cost'],n+2);self.assertLess(r['cost'],baseline)

    def test_no_current_label_leakage(self):
        values=[]
        for outcome in (0,1):
            states=[]
            def hook(t,v,i,state):
                if t==0:states.append((v,i,state['seen'].copy(),state['sums'].copy()))
            run(2,2,lambda v,i:outcome,np.array([[0,1]]),np.full((2,2),.5),hook=hook)
            values.append(states[0])
        for a,b in zip(*values):np.testing.assert_array_equal(a,b)

    def test_exact_ties(self):
        r=run(3,3,lambda v,i:int(i==0),np.array([[0,1],[0,2]]),np.full((3,3),.5))
        np.testing.assert_array_equal(r['decisions'],[0,0]);self.assertEqual(r['cost'],9)

    def test_retrospective_remaining_mean_substitution_fails(self):
        # Literal categorical KT substitution, not the published full implementation.
        population=(0,1)
        for first in population:
            true_counts=[1,1];observed=[int(first==0),int(first==1)]
            denominator=F(true_counts[first]-observed[first],1)
            kt_numerator=F(1,2)
            self.assertEqual(denominator,0);self.assertGreater(kt_numerator,0)

    def test_observed_order_does_not_identify_full_pool_sign(self):
        a=np.array([[1,0],[0,1]]);b=np.array([[1,1],[0,0]])
        np.testing.assert_array_equal(a[:,0],b[:,0])
        self.assertEqual(np.sign(a[0].sum()-a[1].sum()),0)
        self.assertEqual(np.sign(b[0].sum()-b[1].sum()),1)


if __name__=='__main__':unittest.main()
