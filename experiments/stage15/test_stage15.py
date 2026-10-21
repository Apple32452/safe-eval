import unittest

import numpy as np

from frontier_experiment import (FRONTIER_METHODS, frontier_utilities,
                                 label_priority, simulate_frontier, verify_lock)
from shared_pilot import make_paths, precommit_permutations


class FrontierAllocationInvariants(unittest.TestCase):
    def setUp(self):
        self.scores=np.array([[1,1,0,1,0,1],
                              [0,1,0,0,1,0],
                              [1,0,1,1,1,0],
                              [0,0,0,1,0,0]],dtype=float)
        self.names=np.array(['A','B','C','D'])
        self.pairs,self.perm=precommit_permutations(self.names,6,'synthetic15',2)
        self.events,self.evidence=make_paths(self.scores,self.pairs,self.perm)

    def test_frozen_sources_and_data_match_lock(self):
        self.assertIn('protocol_commit',verify_lock())

    def test_frontier_utility_counts_shared_labels_exactly(self):
        pairs=np.array([[0,1],[0,2],[1,2]],dtype=np.int16)
        perm=np.array([[3,0],[3,1],[4,2]],dtype=np.int16)
        cursor=np.zeros(3,dtype=np.int32)
        decision=np.full(3,2,dtype=np.int8)
        seen=np.zeros((3,5),dtype=bool)
        evidence=np.zeros((3,2),dtype=np.int64)
        count,_=frontier_utilities(cursor,decision,seen,pairs,perm,evidence,
                                   'frontier_count')
        self.assertEqual(count[(0,3)],2)
        self.assertEqual(count[(1,3)],1)
        self.assertEqual(count[(2,4)],1)
        weighted,_=frontier_utilities(cursor,decision,seen,pairs,perm,evidence,
                                      'frontier_evidence')
        self.assertEqual(weighted[(0,3)],2*2**20)

    def test_unique_labels_and_exact_full_pool_conclusions(self):
        priority=np.arange(self.scores.size).reshape(self.scores.shape)
        truth=np.sign(self.scores[self.pairs[:,0]].sum(axis=1)-
                      self.scores[self.pairs[:,1]].sum(axis=1))
        for repeat in range(2):
            for method in FRONTIER_METHODS:
                snapshots,acquired,cursor,decision=simulate_frontier(
                    self.scores,self.pairs,self.perm[:,repeat],
                    self.events[:,repeat],self.evidence[:,repeat],method,
                    priority,fractions=(.25,.5,.75,1.0))
                self.assertEqual(len(acquired),len(set(acquired)))
                self.assertEqual(snapshots[-1]['correct'],len(self.pairs))
                self.assertEqual(snapshots[-1]['wrong'],0)
                np.testing.assert_array_equal(decision,truth)

    def test_unrevealed_label_cannot_change_earlier_acquisitions(self):
        priority=label_priority(4,6,'synthetic15',0)
        for method in FRONTIER_METHODS:
            original=simulate_frontier(
                self.scores,self.pairs,self.perm[:,0],self.events[:,0],
                self.evidence[:,0],method,priority,fractions=(.25,))
            unseen=next((s,i) for s in range(4) for i in range(6)
                        if (s,i) not in original[1])
            modified=self.scores.copy()
            modified[unseen]=1-modified[unseen]
            events,evidence=make_paths(modified,self.pairs,self.perm)
            changed=simulate_frontier(
                modified,self.pairs,self.perm[:,0],events[:,0],evidence[:,0],
                method,priority,fractions=(.25,))
            self.assertEqual(original[1],changed[1])
            np.testing.assert_array_equal(original[2],changed[2])
            np.testing.assert_array_equal(original[3],changed[3])

    def test_tie_priority_is_deterministic_and_outcome_independent(self):
        first=label_priority(4,6,'synthetic15',1)
        second=label_priority(4,6,'synthetic15',1)
        np.testing.assert_array_equal(first,second)
        self.assertEqual(len(np.unique(first)),first.size)


if __name__=='__main__':
    unittest.main()
