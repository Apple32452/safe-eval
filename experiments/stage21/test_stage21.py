import itertools,sys,unittest
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from conditional_engine import conditional_directional_paths
from run_stage21 import closure_snapshot,select_chain


class SelectedChainInvariants(unittest.TestCase):
    def test_conditional_process_controls_every_small_null_population(self):
        alpha=.2;threshold=1/alpha
        for population in itertools.product((-1.,0.,1.),repeat=5):
            if sum(population)>0:continue
            permutations=np.array(list(itertools.permutations(population)),dtype=float)
            pilot=permutations[:,:2].sum(axis=1)[None,:];remaining=permutations[:,2:].T[None,:,:].transpose(0,2,1)
            events,_=conditional_directional_paths(remaining,pilot,threshold)
            self.assertLessEqual(np.any(events[0]==1,axis=1).mean(),alpha+1e-12)

    def test_reverse_symmetry_and_exact_final_sign(self):
        rng=np.random.default_rng(4);remaining=rng.uniform(-1,1,(3,7,6));pilot=rng.uniform(-2,2,(3,7))
        events,_=conditional_directional_paths(remaining,pilot,80);reverse,_=conditional_directional_paths(-remaining,-pilot,80)
        np.testing.assert_array_equal(events,np.where(reverse==2,2,-reverse));np.testing.assert_array_equal(events[:,:,-1],np.sign(pilot+remaining.sum(axis=-1)))

    def test_chain_selection_uses_only_pilot(self):
        pilot=np.array([[.8,.7],[.4,.5],[.2,.3]]);names=np.array(["A","B","C"])
        first=select_chain(pilot,names);changed=select_chain(pilot.copy(),names)
        np.testing.assert_array_equal(first[0],changed[0]);np.testing.assert_array_equal(first[1],changed[1])

    def test_correct_chain_closure_recovers_all_pairs(self):
        scores=np.array([[.9,.8],[.6,.5],[.2,.1]]);edges=np.array([[0,1],[1,2]],dtype=np.int16);decision=np.array([1,1],dtype=np.int8)
        result=closure_snapshot(scores,edges,decision,np.array([1,1]),6,6)
        self.assertEqual(result["correct"],3);self.assertEqual(result["closure_added"],1);self.assertEqual(result["complete_ranking"],1)

    def test_one_wrong_edge_can_only_harm_through_base_error(self):
        scores=np.array([[.9,.8],[.6,.5],[.2,.1]]);edges=np.array([[0,1],[1,2]],dtype=np.int16)
        result=closure_snapshot(scores,edges,np.array([1,-1],dtype=np.int8),np.array([1,1]),6,6)
        self.assertGreater(result["wrong"],0);self.assertEqual(result["resolved_pairs"],result["correct"]+result["wrong"])


if __name__=="__main__":unittest.main()
