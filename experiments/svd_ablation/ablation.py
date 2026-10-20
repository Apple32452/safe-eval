"""Isolated feature ablation of the unchanged Stage 9 prediction engine."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
for stage in ('stage7', 'stage8', 'stage9'):
    sys.path.insert(0, str(ROOT.parent / stage))

from safe_eval_v1 import reference_features


def load_engine(use_svd):
    # Separate module globals: never patch the imported canonical engine.
    spec = importlib.util.spec_from_file_location(
        '_svd_ablation_' + str(use_svd), ROOT.parent / 'stage9' / 'stage9_engine.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not use_svd:
        module.reference_features = lambda h: reference_features(h, rank=0)
    return module.evaluate


def evaluate_arm(history, outcomes, repeats, seed, raw, calibrated, alpha,
                 use_svd, forced_ledger=None, pruned=False):
    from wmt_experiment import QueryOracle
    selected_mu = []

    def observe(t, indices, state):
        # Called before the oracle; record only predictions already committed.
        selected_mu.append(state['mu'][np.arange(repeats), indices].copy())

    if pruned:
        from pruned_engine import evaluate
        trace = evaluate(history, QueryOracle(outcomes, repeats), repeats, seed,
                         raw, calibrated, alpha, use_svd, prequery_hook=observe)
    else:
        trace = load_engine(use_svd)(history, QueryOracle(outcomes, repeats), repeats,
                                    seed, raw, calibrated, alpha,
                                    forced_ledger=forced_ledger, prequery_hook=observe)
    residual = outcomes[trace['selected']] - np.asarray(selected_mu)
    # Population variance of prequential residuals within each full query path.
    metrics = dict(mse=np.mean(residual ** 2, axis=0),
                   mae=np.mean(np.abs(residual), axis=0),
                   residual_mean=np.mean(residual, axis=0),
                   residual_variance=np.var(residual, axis=0, ddof=0))
    return trace, metrics
