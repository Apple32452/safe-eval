import itertools
import sys
import unittest
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(HERE.parent/"stage17"))
from run_stage17 import simulate_uniform
from run_stage20 import simulate_pruned


def fixture():
    scores=np.array([[.9,.8,.7,.6,.5],[.7,.6,.5,.4,.3],[.5,.4,.3,.2,.1],[.3,.2,.1,.0,.2]])
    pairs=np.asarray(list(itertools.combinations(range(4),2)),dtype=np.int16)
    path=np.tile(np.arange(5),(len(pairs),1))
    priority=np.arange(scores.size).reshape(5,4).T
    truth=np.sign(scores[pairs[:,0]].sum(axis=1)-scores[pairs[:,1]].sum(axis=1)).astype(np.int8)
    return scores,pairs,path,priority,truth


class ActiveSystemPruningInvariants(unittest.TestCase):
    def test_pruning_matches_control_when_nothing_resolves_early(self):
        scores,pairs,path,priority,truth=fixture(); events=np.full((len(pairs),5),2,dtype=np.int8); events[:,-1]=truth
        fractions=tuple(i/scores.size for i in range(1,scores.size+1))
        control=simulate_uniform(scores,pairs,path,events,priority,fractions=fractions)
        pruned=simulate_pruned(scores,pairs,path,events,priority,fractions=fractions)
        self.assertEqual(control[0],pruned[0]); self.assertEqual(control[1],pruned[1])

    def test_pathwise_resolved_count_dominates_every_budget(self):
        scores,pairs,path,priority,truth=fixture(); events=np.full((len(pairs),5),2,dtype=np.int8)
        crossing=np.array([0,1,2,3,4,4])
        for pair_index,time in enumerate(crossing): events[pair_index,time:]=truth[pair_index]
        fractions=tuple(i/scores.size for i in range(1,scores.size+1))
        control=simulate_uniform(scores,pairs,path,events,priority,fractions=fractions)[0]
        pruned=simulate_pruned(scores,pairs,path,events,priority,fractions=fractions)[0]
        self.assertTrue(all(a["resolved_pairs"]>=b["resolved_pairs"] for a,b in zip(pruned,control)))

    def test_current_item_active_set_is_committed_before_outcomes(self):
        scores,pairs,path,priority,truth=fixture(); events=np.full((len(pairs),5),2,dtype=np.int8)
        events[:,0:]=truth[:,None]
        result=simulate_pruned(scores,pairs,path,events,priority,fractions=(.2,))
        self.assertEqual(result[1],[(0,0),(1,0),(2,0),(3,0)])

    def test_full_budget_is_unique_and_exact(self):
        scores,pairs,path,priority,truth=fixture(); events=np.full((len(pairs),5),2,dtype=np.int8); events[:,-1]=truth
        snapshots,acquired,_,decision=simulate_pruned(scores,pairs,path,events,priority,fractions=(1.0,))
        self.assertEqual(len(acquired),len(set(acquired))); self.assertEqual(snapshots[0]["wrong"],0)
        np.testing.assert_array_equal(decision,truth)

    def test_noncommon_pair_paths_are_rejected(self):
        scores,pairs,path,priority,truth=fixture(); path[0]=path[0,::-1]
        events=np.full((len(pairs),5),2,dtype=np.int8); events[:,-1]=truth
        with self.assertRaises(ValueError): simulate_pruned(scores,pairs,path,events,priority)


if __name__=="__main__": unittest.main()
