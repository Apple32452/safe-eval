from __future__ import annotations
from collections import Counter
from fractions import Fraction
import itertools
import math
import unittest
import numpy as np
from calibrate_stage10 import (pointwise_intervals,repaired_counts,
                               fine_search,exact_risk,risk_record)
from repair_reference import explicit_repaired_counts
from calibration_control import evaluate_control,parent_gates,replay_control


def enumerate_survivors(calibrated,raw):
    n=len(raw)-1
    live=[0]*(n+1)
    for bits in itertools.product((0,1),repeat=n):
        truth=sum(bits);s=0;rl=cl=0;ru=cu=n;covered=True
        for t,y in enumerate(bits,1):
            s+=y
            rl=max(rl,int(raw[t,s,0]));ru=min(ru,int(raw[t,s,1]))
            cl=max(cl,int(calibrated[t,s,0]));cu=min(cu,int(calibrated[t,s,1]))
            lo,hi=(rl,ru) if cl>cu else (cl,cu)
            if t==n:lo=hi=truth
            covered &= lo<=truth<=hi
        live[truth]+=int(covered)
    return live


class StageTenInvariants(unittest.TestCase):
    def test_repaired_counts_match_every_small_binary_string_and_independent_states(self):
        for n in range(2,10):
            raw=pointwise_intervals(n,20)
            for h in (2,3.5,7,20):
                cal=pointwise_intervals(n,h)
                record=repaired_counts(cal,raw)
                self.assertEqual(record['status'],'complete')
                live=[int(v) for v in record['surviving_strings']]
                self.assertEqual(live,enumerate_survivors(cal,raw))
                self.assertEqual(live,explicit_repaired_counts(cal,raw))
                original,_=risk_record(n,h,cal)
                self.assertTrue(all(a>=int(b) for a,b in zip(live,original['surviving_strings'])))

    def test_caps_never_produce_a_risk_certificate(self):
        raw=pointwise_intervals(10,20);cal=pointwise_intervals(10,3)
        for limits in ((1,10000),(10000,1)):
            r=repaired_counts(cal,raw,*limits)
            self.assertEqual(r['status'],'capped')
            self.assertNotIn('surviving_strings',r)
            self.assertNotIn('risk_numerator',r)

    def test_fine_search_bracket_and_mathematical_monotonicity(self):
        n=24
        h=next(h for h in range(2,21) if exact_risk(risk_record(n,h)[0])<=Fraction(1,20))
        r,safe,unsafe=fine_search(n,h,rounds=4)
        self.assertLessEqual(exact_risk(r['safe']),Fraction(1,20))
        self.assertGreater(exact_risk(r['unsafe']),Fraction(1,20))
        self.assertEqual(Fraction(r['safe_fraction'])-Fraction(r['unsafe_fraction']),Fraction(1,16))
        self.assertTrue(np.all(unsafe[:,:,0]>=safe[:,:,0]))
        self.assertTrue(np.all(unsafe[:,:,1]<=safe[:,:,1]))

    def test_fallback_prevents_inferring_risk_monotonicity_from_nested_sets(self):
        # A nested finite-state counterexample: first exit of true K=0 can
        # empty the smaller set, whose fallback covers, while the larger set
        # remains nonempty and wrong. It is not claimed as a PPR instance.
        n=4
        raw=np.full((n+1,n+1,2),-1,dtype=np.int16)
        for t in range(n+1):
            for s in range(t+1):raw[t,s]=(s,s+n-t)
        small=raw.copy();large=raw.copy()
        small[1,0]=(0,0);large[1,0]=(0,1)
        small[2,0]=large[2,0]=(1,1)
        a=enumerate_survivors(small,raw);b=enumerate_survivors(large,raw)
        self.assertEqual(a[0],1);self.assertEqual(b[0],0)
        self.assertEqual([int(v) for v in repaired_counts(small,raw)['surviving_strings']],a)

    def test_control_replay_containment_unique_queries_and_exact_final_mean(self):
        rng=np.random.default_rng(20261017);n=32;repeats=9
        y=rng.integers(0,2,n)
        ledger=np.stack([rng.permutation(n) for _ in range(repeats)],axis=1)
        raw=pointwise_intervals(n,20);fine=pointwise_intervals(n,12.5)
        c,flags=evaluate_control(y,ledger,raw,fine)
        parent_raw=parent_gates(n,20);parent_fine=parent_gates(n,12.5)
        np.testing.assert_array_equal(parent_raw,raw)
        np.testing.assert_array_equal(parent_fine,fine)
        reference,rflags=replay_control(y,ledger,parent_raw,parent_fine)
        np.testing.assert_array_equal(c,reference);np.testing.assert_array_equal(flags,rflags)
        rc,_=evaluate_control(y,ledger,raw,raw)
        nonempty=c[1]>=c[0]
        self.assertTrue(np.all((c[0]>=rc[0])[nonempty]))
        self.assertTrue(np.all((c[1]<=rc[1])[nonempty]))
        np.testing.assert_array_equal(c[:,-1],np.full((2,repeats),int(y.sum())))
        stop=lambda curve:((curve[1]>=curve[0])&(10*(curve[1]-curve[0])<=n)).argmax(axis=0)+1
        self.assertTrue(np.all(stop(c)<=stop(rc)))
        bad=ledger.copy();bad[1]=bad[0]
        with self.assertRaises(ValueError):evaluate_control(y,bad,raw,fine)
        with self.assertRaises(ValueError):evaluate_control(y*.9,ledger,raw,fine)

    def test_repaired_control_is_model_free_and_current_state_uses_only_prefix(self):
        n=12;rng=np.random.default_rng(17)
        ledger=np.arange(n)[:,None];raw=pointwise_intervals(n,20);cal=pointwise_intervals(n,3)
        a=rng.integers(0,2,n);b=a.copy();b[6:]=1-b[6:]
        ca,_=evaluate_control(a,ledger,raw,cal);cb,_=evaluate_control(b,ledger,raw,cal)
        np.testing.assert_array_equal(ca[:,:6],cb[:,:6])


if __name__=='__main__':unittest.main()
