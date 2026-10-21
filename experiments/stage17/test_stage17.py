import itertools
import sys
import unittest
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from continuous_engine import directional_paths
from prepare_scores import build_matrices,mean_score
from run_stage17 import frontier_utilities,simulate_frontier,simulate_uniform


class SharedLabelContributionInvariants(unittest.TestCase):
    def test_mean_score_and_alignment_are_outcome_independent(self):
        self.assertEqual(mean_score([{'score':20},{'score':80}]),.5)
        def annotations(value): return [{'score':value}]
        records={'x-y':{f'x-y_#_d_#_{i}':{'A':annotations(i%101),'B':annotations(80),
                  'C':annotations(40),**({'D':annotations(100)} if i<29 else {})} for i in range(30)}}
        matrices,report=build_matrices(records)
        scores,names,items=matrices['x-y']
        self.assertEqual(names.tolist(),['A','B','C']); self.assertEqual(scores.shape,(3,30))
        self.assertTrue(report[0]['included'])

    def test_betting_factors_control_every_small_null_population(self):
        alpha=.2; threshold=1/alpha
        for population in itertools.product((-1.0,0.0,1.0),repeat=5):
            if sum(population)>0: continue
            permutations=np.array(list(itertools.permutations(population)),dtype=float)
            events,_=directional_paths(permutations[None,:,:],threshold)
            wrong=np.any(events[0]==1,axis=1)
            self.assertLessEqual(wrong.mean(),alpha+1e-12)

    def test_reverse_symmetry_and_exact_final_sign(self):
        rng=np.random.default_rng(7); differences=rng.uniform(-1,1,(4,9,8))
        events,evidence=directional_paths(differences,80)
        reverse,reverse_evidence=directional_paths(-differences,80)
        np.testing.assert_array_equal(events,np.where(reverse==2,2,-reverse))
        np.testing.assert_allclose(evidence,reverse_evidence)
        np.testing.assert_array_equal(events[:,:,-1],np.sign(differences.sum(axis=-1)))

    def test_frontier_utility_is_exact_one_step_potential_drop(self):
        pairs=np.array([[0,1],[0,2],[1,2]],dtype=np.int16)
        permutation=np.array([[0,1],[0,1],[1,0]],dtype=np.int32)
        cursor=np.array([1,1,0],dtype=np.int32); decision=np.full(3,2,dtype=np.int8)
        seen=np.zeros((3,2),dtype=bool); evidence=np.array([[4,7],[2,5],[0,0]],dtype=float)
        utility,active=frontier_utilities(cursor,decision,seen,pairs,permutation,evidence,
                                          'frontier_evidence',threshold=100)
        weights=[]
        for pair_index in active:
            weights.append(1+(evidence[pair_index,cursor[pair_index]-1] if cursor[pair_index] else 0))
        for label,value in utility.items():
            direct=sum(weight for pair_index,weight in zip(active,weights)
                       if label[0] in pairs[pair_index] and label[1]==permutation[pair_index,cursor[pair_index]])
            self.assertEqual(value,direct)

    def test_all_schedulers_use_unique_labels_and_reach_exact_truth(self):
        scores=np.array([[.9,.8,.1,.7],[.2,.3,.8,.1],[.7,.4,.6,.8]])
        pairs=np.array([[0,1],[0,2],[1,2]],dtype=np.int16)
        permutation=np.tile(np.arange(4),(3,1)); events=np.full((3,4),2,dtype=np.int8)
        truth=np.sign(scores[pairs[:,0]].sum(axis=1)-scores[pairs[:,1]].sum(axis=1)); events[:,-1]=truth
        evidence=np.zeros((3,4)); priority=np.arange(scores.size).reshape(scores.shape)
        for result in (simulate_uniform(scores,pairs,permutation,events,priority,fractions=(1.0,)),
                       simulate_frontier(scores,pairs,permutation,events,evidence,'frontier_evidence',
                                         priority,120,fractions=(1.0,))):
            snapshots,acquired,cursor,decision=result
            self.assertEqual(len(acquired),len(set(acquired)))
            self.assertEqual(snapshots[0]['wrong'],0)
            np.testing.assert_array_equal(decision,truth)


if __name__=='__main__': unittest.main()
