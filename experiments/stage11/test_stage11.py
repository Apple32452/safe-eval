from __future__ import annotations
from fractions import Fraction
import itertools
import math
import unittest
import numpy as np
from boosting import Q,B,next_pair,hull,evaluate
from boost_reference import rational_pair,replay
from stage11_common import integer_decisions
from binary_control import ppr_interval


def raw_trace(y,ledger):
    n,repeats=ledger.shape;s=np.zeros(repeats,dtype=int)
    lower=np.zeros(repeats);upper=np.ones(repeats);out=[]
    for t in range(1,n+1):
        s+=y[ledger[t-1]]
        lo,hi=ppr_interval(s,t,n)
        lower=np.maximum(lower,lo);upper=np.minimum(upper,hi)
        out.append(np.rint(np.stack([lower,upper])*n).astype(np.int16))
    result=np.stack(out,axis=1);result[:,-1]=s[None,:]
    return result


class StageElevenInvariants(unittest.TestCase):
    def test_conditional_expectation_and_flooring_match_rational_reference(self):
        for r in range(1,12):
            for a in range(r+1):
                for u,d in ((1,2),(1,7),(6,7)):
                    for w in (0,1,Q,B//3,B-1):
                        for boost in (False,True):
                            pair=next_pair(np.array(w,dtype=np.int64),np.array(a),r,np.array(u),d,boost)
                            actual=tuple(int(v) for v in pair)
                            self.assertEqual(actual,rational_pair(w,a,r,u,d,boost))
                            expectation=Fraction(r-a,r)*actual[0]+Fraction(a,r)*actual[1]
                            self.assertLessEqual(expectation,w)

    def test_every_small_binary_path_has_valid_error_and_independent_replay(self):
        for n in range(2,10):
            bits=np.array(list(itertools.product((0,1),repeat=n)),dtype=int).T
            # A pool of all binary strings, each ledger selects one complete string.
            # Evaluate each possible total through a fixed pool and every permutation
            # outcome string, representing equal-probability paths under that total.
            for k in range(n+1):
                paths=bits[:,bits.sum(axis=0)==k]
                y=np.array([1]*k+[0]*(n-k));ledger=np.empty_like(paths)
                for j in range(paths.shape[1]):
                    one=iter(range(k));zero=iter(range(k,n))
                    ledger[:,j]=[next(one) if b else next(zero) for b in paths[:,j]]
                raw=raw_trace(y,ledger);result=evaluate(y,ledger,raw);reference=replay(y,ledger,raw)
                for key in result:np.testing.assert_array_equal(result[key],reference[key])
                self.assertTrue(np.all(result['rejection_time'][1]<=result['rejection_time'][0]))
                for m in range(2):
                    d=integer_decisions(result['counts'][m],y,result['repaired'][m])
                    failed=int((d['simultaneous_coverage']==0).sum())
                    self.assertLessEqual(Fraction(failed,math.comb(n,k)),Fraction(1,20))

    def test_actual_pool_integer_products_and_boundary_cases(self):
        rng=np.random.default_rng(11017)
        for n in (154,589,820):
            self.assertLess(B*(n+1)**2,2**63)
            for _ in range(250):
                t=int(rng.integers(1,n+1));r=n-t+1;s=int(rng.integers(0,t))
                a=int(rng.integers(0,r+1));w=int(rng.integers(0,B))
                for boost in (False,True):
                    pair=next_pair(np.array(w,dtype=np.int64),np.array(a),r,np.array(s+1),t+1,boost)
                    self.assertEqual(tuple(int(v) for v in pair),rational_pair(w,a,r,s+1,t+1,boost))

    def test_matched_containment_stops_full_mean_and_independent_random_replay(self):
        rng=np.random.default_rng(1711);n=48
        for y in (np.zeros(n,dtype=int),np.ones(n,dtype=int),rng.integers(0,2,n)):
            ledger=np.stack([rng.permutation(n) for _ in range(25)],axis=1)
            raw=raw_trace(y,ledger);r=evaluate(y,ledger,raw);ref=replay(y,ledger,raw)
            for key in r:np.testing.assert_array_equal(r[key],ref[key])
            c=r['counts'];valid=c[1,1]>=c[1,0]
            self.assertTrue(np.all((c[1,0]>=c[0,0])[valid]))
            self.assertTrue(np.all((c[1,1]<=c[0,1])[valid]))
            dg=integer_decisions(c[0],y,r['repaired'][0]);db=integer_decisions(c[1],y,r['repaired'][1])
            self.assertTrue(np.all(db['stop_queries']<=dg['stop_queries']))
            self.assertTrue(np.all(c[:,:,-1]==int(y.sum())))

    def test_all_candidates_inverted_holes_are_conservatively_hulled(self):
        alive=np.array([[False,True,False,True,False],[False]*5])
        lo,hi,empty,holes=hull(alive)
        self.assertEqual((lo[0],hi[0],holes[0]),(1,3,1))
        self.assertTrue(empty[1]);self.assertEqual(holes[1],0)

    def test_prefix_predictability_and_invalid_queries(self):
        n=24;ledger=np.arange(n)[:,None];a=np.arange(n)%2;b=a.copy();b[12:]=1-b[12:]
        ra=evaluate(a,ledger,raw_trace(a,ledger));rb=evaluate(b,ledger,raw_trace(b,ledger))
        np.testing.assert_array_equal(ra['counts'][:,:,:12],rb['counts'][:,:,:12])
        np.testing.assert_array_equal(ra['repaired'][:,:12],rb['repaired'][:,:12])
        for y,l in ((a*.8,ledger),(a,np.zeros_like(ledger)),(a,ledger.astype(float))):
            with self.assertRaises(ValueError):evaluate(y,l,raw_trace(a,ledger))
        with self.assertRaises(ValueError):evaluate(np.zeros(821),np.arange(821)[:,None],np.zeros((2,821,1),dtype=int))


if __name__=='__main__':unittest.main()
