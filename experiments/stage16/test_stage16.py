import sys
import unittest
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from external_engine import Q,raw_evidence
from prepare_wmt25 import build_matrices,is_reference,strict_outcome
from run_stage16 import frontier_utilities,simulate_frontier


class ExternalValidationInvariants(unittest.TestCase):
    def test_reference_filter_and_strict_consensus(self):
        self.assertTrue(is_reference('refA')); self.assertTrue(is_reference('Human-B'))
        self.assertFalse(is_reference('CommandA-MT'))
        self.assertEqual(strict_outcome([{'score':100,'errors':[]}]),1)
        self.assertEqual(strict_outcome([{'score':100,'errors':[]},{'score':99,'errors':[]}]),0)
        self.assertEqual(strict_outcome([{'score':100,'errors':[{'severity':'minor'}]}]),0)
        self.assertEqual(strict_outcome([{'score':100,'errors':[{'severity':'undecided'}]}]),0)

    def test_max_coverage_selection_does_not_use_outcomes(self):
        def a(value): return [{'score':100 if value else 0,'errors':[] if value else [{'severity':'major'}]}]
        records={'xx-yy':{f'xx-yy_#_d_#_{i}':{'A':a(i%2),'B':a(1),'C':a(0),**({'D':a(1)} if i<29 else {})} for i in range(30)}}
        matrices,report=build_matrices(records)
        scores,names,items=matrices['xx-yy']
        self.assertEqual(names.tolist(),['A','B','C'])
        self.assertEqual(scores.shape,(3,30)); self.assertTrue(report[0]['included'])

    def test_generic_raw_matches_stage13_at_its_cap(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'stage13'))
        from paired_engine import raw_evidence as old_raw
        for n in range(2,9):
            for t in range(n+1):
                for pos in range(t+1):
                    for neg in range(t-pos+1):
                        eq=t-pos-neg
                        new=raw_evidence(n,[pos],[neg],[eq],9480)
                        old=old_raw(n,[pos],[neg],[eq])
                        np.testing.assert_array_equal(new,old)

    def test_parser_rejects_unknown_retained_severity(self):
        with self.assertRaises(ValueError):
            strict_outcome([{'score':50,'errors':[{'severity':'critical'}]}])

    def test_external_frontier_uses_language_specific_cap(self):
        pairs=np.array([[0,1],[0,2]],dtype=np.int16)
        permutation=np.tile(np.arange(2,dtype=np.int32),(2,1))
        cursor=np.ones(2,dtype=np.int32)
        decision=np.array([2,2],dtype=np.int8)
        seen=np.zeros((3,2),dtype=bool)
        evidence=np.array([[500*Q],[50*Q]],dtype=np.int64)
        utility,_=frontier_utilities(cursor,decision,seen,pairs,permutation,
                                     evidence,cap_units=100)
        self.assertEqual(utility[(0,1)],2*Q+150*Q)
        self.assertEqual(utility[(1,1)],Q+100*Q)
        self.assertEqual(utility[(2,1)],Q+50*Q)

    def test_frontier_simulation_has_unique_cost_and_exact_final_truth(self):
        scores=np.array([[1,1,0,1],[0,0,1,0],[1,0,1,1]],dtype=np.int8)
        pairs=np.array([[0,1],[0,2],[1,2]],dtype=np.int16)
        permutation=np.tile(np.arange(4,dtype=np.int32),(3,1))
        events=np.full((3,4),2,dtype=np.int8)
        truth=np.sign(scores[pairs[:,0]].sum(axis=1)-scores[pairs[:,1]].sum(axis=1))
        events[:,-1]=truth
        evidence=np.zeros((3,4),dtype=np.int64)
        priority=np.arange(scores.size,dtype=np.int64).reshape(scores.shape)
        snapshots,acquired,cursor,decision=simulate_frontier(
            scores,pairs,permutation,events,evidence,priority,cap_units=120,
            fractions=(1.0,))
        self.assertEqual(len(acquired),len(set(acquired)))
        self.assertEqual(snapshots[0]['wrong'],0)
        np.testing.assert_array_equal(decision,truth)
        np.testing.assert_array_equal(cursor,np.full(3,4))


if __name__=='__main__': unittest.main()
