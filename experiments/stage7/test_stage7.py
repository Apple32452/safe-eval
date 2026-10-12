"""New adapter checks; previous Stage 3/5/PPR statistical tests are preserved."""
import hashlib
import json
from pathlib import Path
import unittest
import numpy as np
from prepare_wmt23 import load_data
from reserve_fallback import evaluate_reserved
from wmt_experiment import QueryOracle
from stage7_experiment import ROOT,build_cases,load_stage6_reference,pack_curves,unpack_curves
from analyze_stage7 import same_confidence_sets

class StageSevenCompatibility(unittest.TestCase):
    def test_confidence_set_audit_matches_enumerated_sets_including_all_empty_representations(self):
        grid=np.arange(6)
        for lo,hi in ((l,u) for l in grid for u in grid):
            actual=set(grid[(grid>=lo)&(grid<=hi)].tolist())
            for other_lo,other_hi in ((l,u) for l in grid for u in grid):
                other=set(grid[(grid>=other_lo)&(grid<=other_hi)].tolist())
                self.assertEqual(same_confidence_sets(np.array([[lo],[hi]]),np.array([[other_lo],[other_hi]])),actual==other)

    def test_statistical_modules_remain_byte_identical_to_stage5(self):
        parent=json.loads((ROOT/'PARENT_RECORDS.json').read_text())
        for name,digest in parent['stage5_code_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)

    def test_all_folds_histories_and_seeds_match_verified_stage6_cases(self):
        datasets,provenance=load_data(ROOT/'data')
        reference,_=load_stage6_reference()
        self.assertEqual([r['matrix_sha256'] for r in provenance['datasets']],reference['matrix_sha256'])
        prior={c['case_id']:c for c in reference['cases']}
        cases=build_cases(datasets)
        self.assertEqual(len(cases),117)
        for case,history,outcomes in cases:
            self.assertNotIn(case['target_system'],case['background_systems'])
            for field in ('n','raw_seed','background_systems','history_sha256'):
                self.assertEqual(case[field],prior[case['case_id']][field])
            self.assertTrue(np.all((outcomes==0)|(outcomes==1)))

    def test_actual_wmt23_raw_paths_and_stops_match_stage6_and_curve_encoding_is_lossless(self):
        datasets,_=load_data(ROOT/'data')
        reference,lookup=load_stage6_reference()
        case,history,outcomes=next(c for c in build_cases(datasets) if c[0]['scenario']=='aligned' and c[0]['language_pair']=='en-de' and c[0]['target_system']=='AIRC')
        repeats=reference['repeats']
        runs,diag=evaluate_reserved(history,QueryOracle(outcomes,repeats),repeats,seed=case['raw_seed'])
        prior=next(c for c in reference['cases'] if c['case_id']==case['case_id'])
        digest=hashlib.sha256(np.asarray(diag['selected'],dtype='<i4').tobytes()).hexdigest()
        self.assertEqual(digest,prior['raw_stream_sha256'])
        np.testing.assert_array_equal(runs['published_ppr95']['stop'],[lookup[(case['case_id'],j)]['raw95'] for j in range(repeats)])
        packed=pack_curves(runs,diag['selected']);curves=unpack_curves(packed)
        for method in runs:
            np.testing.assert_array_equal(curves[method][0],runs[method]['lower'])
            np.testing.assert_array_equal(curves[method][1],runs[method]['upper'])

    def test_stage6_paired_reference_is_complete_and_query_budgets_hold(self):
        reference,lookup=load_stage6_reference()
        self.assertEqual(len(lookup),11700)
        for case in reference['cases']:
            for j in range(reference['repeats']):
                row=lookup[(case['case_id'],j)]
                for method in ('active10','random10'):
                    self.assertLessEqual(row[method],min(case['n'],row['raw95']+row['raw95']//10))

if __name__=='__main__':unittest.main()
