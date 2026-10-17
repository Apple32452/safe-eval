import itertools
import math
from fractions import Fraction
from pathlib import Path
import sys
import unittest
import numpy as np
from certify_stage9 import pointwise_intervals, surviving_counts
from rounded_betting import (prediction_bounds, ratio_bounds, stakes, lower_factors,
                             ScaledCapital, average_crossed, down)
from stage9_engine import evaluate
from replay_stage9 import backward_failures,binomial_rows,replay

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"stage8"))
from stage8_engine import evaluate_matched
from stage8_common import verify_protocol, build_cases
from wmt_experiment import QueryOracle

F=lambda x: Fraction.from_float(float(x))


class StageNineInvariants(unittest.TestCase):
    def test_integer_certificate_matches_exhaustive_binary_strings(self):
        for n in range(2,10):
            for threshold in (2,5,20):
                table=pointwise_intervals(n,threshold)
                expected=[0]*(n+1)
                for bits in itertools.product((0,1),repeat=n):
                    k=sum(bits);s=0;alive=True
                    for t,y in enumerate(bits,1):
                        s+=y
                        alive &= table[t,s,0]<=k<=table[t,s,1]
                    expected[k]+=int(alive)
                actual,_=surviving_counts(table)
                self.assertEqual(actual,expected)
                choose=binomial_rows(n)
                for k in range(n+1):
                    self.assertEqual(backward_failures(table,k,choose),math.comb(n,k)-actual[k])

    def test_outward_factors_bound_exact_rational_unit_mean_factors(self):
        rng=np.random.default_rng(762)
        n=9
        qlo,qhi=ratio_bounds(np.arange(n+1),n)
        for _ in range(15):
            mu=rng.uniform(.1,.9,(1,n))
            unseen=np.ones((1,n),dtype=bool);unseen[:,:2]=False
            s=np.array([2]);r=n-2
            outcomes=rng.integers(0,2,n)
            theta=Fraction(2+int(outcomes[2:].sum()),n)
            alo,bhi,_=prediction_bounds(s,unseen,mu,None,None)
            lp,lm=stakes(alo,bhi,qlo,qhi,np.array([.7]))
            unit_plus=Fraction(0);unit_minus=Fraction(0)
            for i in range(2,n):
                y=np.array([outcomes[i]])
                zlo,zhi=prediction_bounds(s,unseen,mu,np.array([i]),y)
                z=(Fraction(2)+sum(F(v) for v in mu[0,2:]))/n+Fraction(r,n)*(int(y[0])-F(mu[0,i]))
                self.assertLessEqual(F(zlo[0]),z);self.assertGreaterEqual(F(zhi[0]),z)
                fp,fm=lower_factors(zlo,zhi,qlo,qhi,lp,lm)
                for k in range(n+1):
                    exactp=1+F(lp[0,k])*(z-Fraction(k,n))
                    exactm=1-F(lm[0,k])*(z-Fraction(k,n))
                    self.assertGreater(exactp,0);self.assertGreater(exactm,0)
                    self.assertLessEqual(F(fp[0,k]),exactp)
                    self.assertLessEqual(F(fm[0,k]),exactm)
                k=int(theta*n)
                unit_plus+=1+F(lp[0,k])*(z-theta)
                unit_minus+=1-F(lm[0,k])*(z-theta)
            self.assertEqual(unit_plus/r,1);self.assertEqual(unit_minus/r,1)

    def test_scaled_capital_and_extreme_alignment_are_conservative(self):
        cap=ScaledCapital((1,1));exact=Fraction(1)
        for value in [.11,1.7,4.2,.9,100.]*30:
            factor=float(value)
            exact*=F(factor)
            cap.update(np.array([[factor]]))
            bounded=F(cap.m[0,0])*Fraction(2)**int(cap.e[0,0])
            self.assertLessEqual(bounded,exact)
        small=ScaledCapital((1,1));small.e[:]=-3000
        big=ScaledCapital((1,1));big.e[:]=3000
        self.assertTrue(average_crossed(big,small,Fraction(1,20))[0,0])
        self.assertFalse(average_crossed(small,small,Fraction(1,20))[0,0])
        near=ScaledCapital((1,1));near.m[:]=.625;near.e[:]=5
        # A true capital of exactly 20 is rounded down before rejection.
        self.assertFalse(average_crossed(near,near,Fraction(1,20))[0,0])

    def test_exact_small_pool_coverage_and_all_path_raw95_cost_bound(self):
        n=6
        permutations=np.asarray(list(itertools.permutations(range(n))),dtype=int).T
        repeats=permutations.shape[1]
        history=np.array([[0,1,0,1,0,1],[1,1,0,0,1,0],[1,0,1,0,1,0]],dtype=float)
        for threshold,delta in ((20,Fraction(1,20)),(5,Fraction(1,5))):
            table=pointwise_intervals(n,threshold)
            alive,_=surviving_counts(table)
            risk=max(Fraction(math.comb(n,k)-alive[k],math.comb(n,k)) for k in range(n+1))
            alpha=delta-risk
            for bits in itertools.product((0,1),repeat=n):
                y=np.asarray(bits)
                trace=evaluate(history,QueryOracle(y,repeats),repeats,3,table,table,alpha,forced_ledger=permutations)
                c=trace["counts"];k=int(y.sum())
                failures=~((c[:,0]<=k)&(c[:,1]>=k)).all(axis=1)
                for method in failures:
                    self.assertLessEqual(Fraction(int(method.sum()),repeats),delta)
                precise=(c[:,1]>=c[:,0])&(10*(c[:,1]-c[:,0])<=n)
                stops=precise.argmax(axis=1)+1
                self.assertTrue(np.all(stops[1:]<=stops[0]))
                self.assertTrue(np.all(c[:,:,-1]==k))

    def test_zero_controls_are_exactly_independent_of_history(self):
        n=12;table=pointwise_intervals(n)
        h=np.random.default_rng(6).integers(0,2,(4,n))
        y=np.arange(n)%2
        first=evaluate(h,QueryOracle(y,5),5,32,table,table,Fraction(1,100))
        second=evaluate(1-h,QueryOracle(y,5),5,32,table,table,Fraction(1,100))
        np.testing.assert_array_equal(first["counts"][:3],second["counts"][:3])
        np.testing.assert_array_equal(first["selected"],second["selected"])

    def test_current_label_cannot_change_own_prediction_support_or_stake(self):
        n=8;table=pointwise_intervals(n)
        h=np.random.default_rng(7).integers(0,2,(4,n))
        snapshots=[]
        for y in (np.zeros(n,dtype=int),np.ones(n,dtype=int)):
            seen=[]
            def hook(t,i,state):
                if t==1:seen.append(state)
            evaluate(h,QueryOracle(y,1),1,1,table,table,Fraction(1,100),prequery_hook=hook)
            snapshots.append(seen[0])
        for key in ("mu","eta","support"):
            np.testing.assert_array_equal(snapshots[0][key],snapshots[1][key])
        for a,b in zip(snapshots[0]["lambdas"],snapshots[1]["lambdas"]):
            for x,y in zip(a,b):np.testing.assert_array_equal(x,y)

    def test_ordinary_raw95_full_curves_match_stage8_on_real_cases(self):
        _,datasets=verify_protocol()
        cases=build_cases(datasets)
        for pair in ("en-de","he-en","zh-en"):
            case,h,y=next(x for x in cases if x[0]["scenario"]=="aligned" and x[0]["language_pair"]==pair)
            n=len(y);table=pointwise_intervals(n)
            trace=evaluate(h,QueryOracle(y,2),2,case["raw_seed"],table,table,Fraction(1,100))
            old,diag=evaluate_matched(h,QueryOracle(y,2),2,case["raw_seed"])
            np.testing.assert_array_equal(trace["selected"],diag["selected"])
            np.testing.assert_array_equal(trace["counts"][0]/n,
                np.stack([old["published_ppr95"]["lower"],old["published_ppr95"]["upper"]]))
            replay(case,h,y,trace,table,Fraction(1,100))

    def test_fractional_target_is_rejected(self):
        n=4;table=pointwise_intervals(n)
        with self.assertRaises(ValueError):
            evaluate(np.full((3,n),.5),lambda indices: np.full(len(indices),.5),
                     1,1,table,table,Fraction(1,100))


if __name__=="__main__":
    unittest.main()
