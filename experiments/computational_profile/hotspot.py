"""Separate cProfile diagnostic; never used for authoritative runtime."""
import cProfile
import json
from pathlib import Path
import pstats
import sys
from benchmark import load, digest
import numpy as np

mod = load('experiments/exact_sequential_probe/sequential_probe.py')
rng = np.random.default_rng(731)
scores = (rng.random((2, 32)) < np.array([.9, .1])[:, None]).astype(np.int8)
profile = cProfile.Profile()
result = profile.runcall(mod.certificate, scores, .9, .1, .5, 731)
out = Path(__file__).resolve().parent / 'results'
stats = pstats.Stats(profile)
rows = []
for (file, line, name), (primitive, calls, exclusive, cumulative, callers) in stats.stats.items():
    rows.append(dict(file=Path(file).name, line=line, name=name, calls=calls,
                     exclusive_s=exclusive, cumulative_s=cumulative))
(out/'exact_hotspot.json').write_text(json.dumps(dict(output_digest=digest(result),
    total_profile_s=stats.total_tt, functions=sorted(rows,key=lambda r:-r['cumulative_s'])),indent=2))
stats.sort_stats('cumulative').print_stats(25)
