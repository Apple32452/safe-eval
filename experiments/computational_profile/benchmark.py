"""Read-only profiling of historical algorithms; run from repository root."""
from __future__ import annotations
import argparse, ast, contextlib, hashlib, importlib.util, itertools, json, os
from pathlib import Path
import platform, subprocess, sys, time, traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for key in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[key] = '1'


def load(relative):
    path = ROOT / relative
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class Phases:
    def __init__(self):
        self.values = {}

    @contextlib.contextmanager
    def measure(self, name):
        start = time.perf_counter()
        try:
            yield
        finally:
            self.values.setdefault(name, []).append(time.perf_counter() - start)


def instrument(mod, function, ranges, phases):
    """Wrap exact original statement ranges in timing contexts, in memory only."""
    import inspect
    tree = ast.parse(inspect.getsource(getattr(mod, function)))
    lines = inspect.getsource(getattr(mod, function)).splitlines()
    spans = []
    for name, first, last in ranges:
        start = next(i + 1 for i, s in enumerate(lines) if s.strip() == first)
        end = next(i + 1 for i, s in enumerate(lines) if s.strip() == last)
        spans.append((name, start, end))

    class Wrap(ast.NodeTransformer):
        def generic_visit(self, node):
            super().generic_visit(node)
            for field, value in ast.iter_fields(node):
                if not isinstance(value, list) or not value or not isinstance(value[0], ast.stmt):
                    continue
                for name, start, end in spans:
                    indices = [i for i, x in enumerate(value)
                               if start <= getattr(x, 'lineno', -1) <= end]
                    if indices and value[indices[0]].lineno == start and value[indices[-1]].end_lineno == end:
                        a, b = indices[0], indices[-1] + 1
                        call = ast.Call(ast.Attribute(ast.Name('_profile_phases', ast.Load()),
                                                     'measure', ast.Load()),
                                        [ast.Constant(name)], [])
                        wrapped = ast.With([ast.withitem(call)], value[a:b])
                        ast.copy_location(wrapped, value[a])
                        value[a:b] = [wrapped]
            return node

    tree = ast.fix_missing_locations(Wrap().visit(tree))
    namespace = dict(mod.__dict__, _profile_phases=phases)
    exec(compile(tree, str(HERE / 'in_memory_instrumentation'), 'exec'), namespace)
    return namespace[function]


def canonical(value):
    import numpy as np
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=canonical).encode()).hexdigest()


def worker(config):
    import numpy as np
    import psutil
    begin = time.perf_counter()
    rng = np.random.default_rng(731)
    phases = Phases()
    kind, s, n = config['kind'], config['s'], config['n']
    extra = {}
    if kind == 'stage22':
        mod = load('experiments/stage22/run_stage22.py')
        pairs = np.array(list(itertools.combinations(range(s), 2)) if config['graph'] == 'complete'
                         else [(0, i) for i in range(1, s)], dtype=np.int16)
        scores = np.full((s, n), .5) if config.get('scenario') == 'tie' else np.clip(
            np.linspace(.1, .9, s)[:, None] + rng.normal(0, .05, (s, n)), 0, 1)
        order = rng.permutation(n)
        perm = np.broadcast_to(order, (len(pairs), n)).copy()
        priority = rng.permutation(s * n).reshape(s, n)
        start = time.perf_counter()
        events, _ = mod.make_paths(scores, pairs, perm[:, None, :], 40 * len(pairs))
        extra['offline_inference_wall_s'] = time.perf_counter() - start
        args = (scores, pairs, perm, events[:, 0, :], priority, config['method'])
        plain = mod.simulate_graph
        profiled = instrument(mod, 'simulate_graph', [
            ('selection', 'if committed_position == len(committed):', 'committed_position += 1'),
            ('inference', 'close_free(seen, cursor, decision, pairs, permutation, events)',
             'close_free(seen, cursor, decision, pairs, permutation, events)')], phases)
        # The same close_free source occurs inside and outside advance_one; wrap both.
    elif kind == 'stage31':
        mod = load('experiments/stage31/run_koehn_panels.py')
        start = time.perf_counter()
        mod.SYSTEMS = s
        mod.PAIRS = np.array(list(itertools.combinations(range(s), 2)), dtype=np.int16)
        mod.PANELS = np.array(list(itertools.combinations(range(s), 5)), dtype=np.int16)
        mod.EDGE_LOOKUP = np.full((s, s), -1, dtype=np.int16)
        mod.EDGE_LOOKUP[mod.PAIRS[:, 0], mod.PAIRS[:, 1]] = np.arange(len(mod.PAIRS))
        mod.PANEL_EDGES = np.array([[mod.EDGE_LOOKUP[a, b] for a, b in itertools.combinations(panel, 2)]
                                  for panel in mod.PANELS], dtype=np.int16)
        extra.update(panel_setup_wall_s=time.perf_counter() - start, enumerated_panels=len(mod.PANELS))
        means = rng.uniform(0, 10, s)
        qualities = rng.normal(means, np.sqrt(10), (n, s))
        candidates = rng.integers(len(mod.PANELS), size=(n, config['candidates']))
        args = (qualities, candidates, means, config['method'])
        plain = mod.run_one
        profiled = instrument(mod, 'run_one', [
            ('selection', 'if method == "uniform_panel":', 'choice = int(candidates[int(np.argmax(unresolved))])'),
            ('inference', 'edges = PANEL_EDGES[choice]', 'state[active[evidence[:, 1] >= threshold]] = -1')], phases)
    else:
        mod = load('experiments/exact_sequential_probe/sequential_probe.py')
        probs = {'strong': (.9, .1), 'moderate': (.7, .3), 'adverse': (.3, .7)}[config['scenario']]
        scores = (rng.random((2, n)) < np.array(probs)[:, None]).astype(np.int8)
        pa, pb = (.7, .3) if config['scenario'] == 'moderate' else (.9, .1)
        args = (scores, pa, pb, config['q'], 731)
        plain = mod.certificate
        profiled = instrument(mod, 'certificate', [
            ('inference', 'plus = Design(seen, known, q, pa, pb)',
             'fminus, fallback_minus = factor(minus, -1)'),
            ('selection', 'i = int(rng.choice(plus.eligible))', 'buy_a = bool(a_unknown)')], phases)
    setup = time.perf_counter() - begin
    rss_ready = psutil.Process().memory_info().rss
    start, cpu = time.perf_counter(), time.process_time()
    result = plain(*args)
    wall, cpu = time.perf_counter() - start, time.process_time() - cpu
    peak_plain = psutil.Process().memory_info().peak_wset
    start = time.perf_counter()
    measured = profiled(*args)
    profiled_wall = time.perf_counter() - start
    assert digest(result) == digest(measured), 'Instrumentation changed outputs'
    steps = result['completion_cost'] if kind == 'stage22' else result['panels'] if kind == 'stage31' else len(result['path'])
    queries = result['cost'] if kind == 'exact' else steps
    summary = {}
    for name, values in phases.values.items():
        summary[name] = dict(total_s=sum(values), calls=len(values), p50_s=float(np.median(values)),
                             p95_s=float(np.quantile(values, .95)), max_s=max(values))
    summary['other'] = dict(total_s=profiled_wall - sum(v['total_s'] for v in summary.values()))
    return dict(config=config, wall_s=wall, cpu_s=cpu, cpu_core_percent=100 * cpu / wall,
                setup_wall_s=setup, ready_rss_bytes=rss_ready, peak_plain_bytes=peak_plain,
                peak_process_bytes=psutil.Process().memory_info().peak_wset,
                profiled_wall_s=profiled_wall, phases=summary, steps=steps, queries=queries,
                output_digest=digest(result), parity=True, complete=result.get('complete', True),
                wrong=result.get('wrong', False), **extra)


def matrix():
    cases = []
    for method in ('star_common', 'star_pruned'):
        for s, n, graph, scenario in [(5,512,'star','strong'), (15,128,'star','strong'),
             (15,512,'star','strong'), (15,2048,'star','strong'), (30,512,'star','strong'),
             (15,512,'complete','strong'), (30,512,'complete','strong'), (15,512,'complete','tie')]:
            cases.append(dict(kind='stage22', s=s,n=n,graph=graph,scenario=scenario,method=method))
    for method in ('uniform_panel', 'unresolved_panel'):
        for s,n,c in [(5,1024,16),(15,256,16),(15,1024,16),(15,6000,16),
                      (30,1024,16),(15,1024,256),(15,1024,1024)]:
            cases.append(dict(kind='stage31',s=s,n=n,candidates=c,method=method))
    for n in (8,16,32,64):
        for q in (1., .5):
            cases.append(dict(kind='exact',s=2,n=n,q=q,scenario='strong',method='exact'))
    for scenario in ('moderate','adverse'):
        cases.append(dict(kind='exact',s=2,n=32,q=.5,scenario=scenario,method='exact'))
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker')
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.loads(args.worker))))
        return
    import psutil
    out = HERE / 'results'
    out.mkdir(exist_ok=True)
    source_paths = ['experiments/stage22/run_stage22.py','experiments/stage17/continuous_engine.py',
                    'experiments/stage17/run_stage17.py','experiments/stage31/run_koehn_panels.py',
                    'experiments/exact_sequential_probe/sequential_probe.py',
                    'experiments/computational_profile/benchmark.py','experiments/computational_profile/PROTOCOL.md']
    manifest = dict(platform=platform.platform(), python=sys.version, logical_cpus=psutil.cpu_count(),
                    physical_cpus=psutil.cpu_count(logical=False), total_memory=psutil.virtual_memory().total,
                    numpy=__import__('numpy').__version__, scipy=__import__('scipy').__version__,
                    source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths},
                    matrix=matrix(), repeats=args.repeats, started=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    with (out/'raw.jsonl').open('w') as handle:
        for i, config in enumerate(matrix()):
            for repeat in range(args.repeats):
                start = time.perf_counter()
                try:
                    child = subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',json.dumps(config)],
                                           capture_output=True,text=True,timeout=120,cwd=ROOT)
                    row = json.loads(child.stdout) if child.returncode == 0 else dict(config=config,error=child.stderr)
                except subprocess.TimeoutExpired:
                    row = dict(config=config,timeout_s=120)
                row.update(repeat=repeat,case=i,subprocess_wall_s=time.perf_counter()-start)
                handle.write(json.dumps(row)+'\n'); handle.flush()
                print(f'{i+1}/{len(matrix())} rep={repeat} {config} wall={row.get("wall_s")} error={row.get("error", "")[:160]}',flush=True)


if __name__ == '__main__':
    main()
