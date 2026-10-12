"""Pinned WMT23 annotations -> aligned exact binary consensus outcomes.

This is a derived recorded-annotation indicator, not official MQM. Quality-
control segments are excluded globally before alignment, never imputed.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import urllib.request
import numpy as np

COMMIT = '29acd6999aaea3586378c9dcb58d8cc4820cede3'
REPOSITORY = 'https://github.com/google/wmt-mqm-human-evaluation'
SOURCES = {
    'en-de': ('generalMT2023/ende/mqm_generalMT2023_ende.tsv',
              '462f7d001fdf9b2a45904ae050899c52dcf41099476565139b218d588e421d5a'),
    'he-en': ('generalMT2023/heen/mqm_generalMT2023_heen.tsv',
              '73a8e66b0de1d0582e09bdcecf6c7324070d50b71789c63f19ad9fc81d3195fb'),
    'zh-en': ('generalMT2023/zhen/mqm_generalMT2023_zhen.tsv',
              'd368e6bd77e00c469ecf92a6f56bf07320ed2fd951661e61580bd8d49708603f'),
}
HEADER = ['system', 'doc', 'docSegId', 'globalSegId', 'rater', 'source',
          'target', 'category', 'severity', 'metadata']
HEADER_COMMENT = '# Documentation: https://github.com/google-research/google-research/tree/master/MAROT_viewer'
ERRORS = {'minor', 'major', 'critical'}
KNOWN = ERRORS | {'no-error', 'neutral', 'hotw-test'}

def source_issue(category):
    return category.strip().casefold().replace('_', ' ') == 'source issue'

def parse_annotations(text):
    lines = text.splitlines()
    header = lines[0].split('\t') if lines else []
    if header != HEADER and header != HEADER + [HEADER_COMMENT]:
        raise ValueError('Unexpected annotation header')
    errors, controls = defaultdict(bool), set()
    severities, count, source_count, neutral_count = Counter(), 0, 0, 0
    for line_number, line in enumerate(lines[1:], 2):
        if not line:
            continue
        fields = line.split('\t')
        if len(fields) != 10:
            raise ValueError(f'Line {line_number}: expected ten literal tab fields')
        system, doc, docseg, globalseg, rater, src, _, category, severity, _ = fields
        if not all((system, doc, rater)) or not docseg.isdigit() or not globalseg.isdigit():
            raise ValueError(f'Line {line_number}: invalid item identity')
        sev = severity.strip().casefold()
        if sev not in KNOWN:
            raise ValueError(f'Line {line_number}: unknown severity {severity!r}')
        item = (doc, int(docseg), int(globalseg))
        count += 1
        severities[sev] += 1
        if sev == 'hotw-test' or doc.casefold() == 'canary' or src.startswith('CANARY GUID'):
            controls.add(item)
            continue
        key = (system, item, rater)
        errors[key] = errors[key]
        source_count += int(source_issue(category))
        neutral_count += int(sev == 'neutral')
        if sev in ERRORS and not source_issue(category):
            errors[key] = True
    ratings = defaultdict(list)
    dropped_ratings = 0
    for (system, item, rater), has_error in errors.items():
        if item in controls:
            dropped_ratings += 1
            continue
        ratings[(system, item)].append(1 - int(has_error))
    systems = defaultdict(dict)
    for (system, item), values in ratings.items():
        systems[system][item] = float(min(values))
    audit = dict(annotation_rows=count, severity_counts=dict(sorted(severities.items())),
                 excluded_control_segments=len(controls), excluded_ordinary_ratings_on_control_segments=dropped_ratings,
                 ignored_source_issue_rows=source_count, ignored_neutral_rows=neutral_count,
                 raters_per_system_item=dict(sorted(Counter(map(len, ratings.values())).items())))
    return dict(systems), audit

def make_matrix(systems):
    references = sorted(s for s in systems if s.casefold().startswith(('ref', 'human')))
    mt = {s: v for s, v in systems.items() if s not in references}
    if len(mt) < 3:
        raise ValueError('Need at least three translation systems')
    common = set.intersection(*(set(v) for v in mt.values()))
    if not common:
        raise ValueError('No commonly annotated segments')
    items = sorted(common, key=lambda i: (i[2], i[0], i[1]))
    if len({i[2] for i in items}) != len(items):
        raise ValueError('Global segment IDs are not unique')
    names = sorted(mt)
    scores = np.array([[mt[s][i] for i in items] for s in names], dtype=float)
    if np.any((scores != 0) & (scores != 1)):
        raise ValueError('Consensus outcomes must be exact binary values')
    return scores, np.array(names), np.array(items, dtype=str), dict(
        translation_systems=len(names), system_names=names, excluded_references=references,
        common_items=len(items), observed_items_per_system={s: len(mt[s]) for s in names},
        removed_noncommon_items_per_system={s: len(mt[s])-len(items) for s in names})

def matrix_hash(scores, names, items):
    h = hashlib.sha256(np.asarray(scores, dtype='<f8').tobytes())
    h.update(json.dumps(names.tolist(), ensure_ascii=False, separators=(',', ':')).encode())
    h.update(json.dumps(items.tolist(), ensure_ascii=False, separators=(',', ':')).encode())
    return h.hexdigest()

def prepare(raw_directory, output_directory, download=False):
    raw_directory, output_directory = Path(raw_directory), Path(output_directory)
    raw_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    records = []
    for pair, (relative, expected) in SOURCES.items():
        path = raw_directory / Path(relative).name
        url = f'https://raw.githubusercontent.com/google/wmt-mqm-human-evaluation/{COMMIT}/{relative}'
        if download:
            with urllib.request.urlopen(url, timeout=90) as response:
                path.write_bytes(response.read())
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != expected:
            raise ValueError(f'Source checksum mismatch: {path}')
        systems, parsed = parse_annotations(payload.decode('utf-8'))
        scores, names, items, alignment = make_matrix(systems)
        np.savez_compressed(output_directory / f'wmt23_{pair}_error_free.npz',
                            scores=scores, systems=names, items=items)
        records.append(dict(language_pair=pair, source_url=url, source_bytes=len(payload),
                            source_sha256=digest, matrix_sha256=matrix_hash(scores, names, items),
                            **parsed, **alignment))
        print(f'{pair}: {len(names)} MT systems x {scores.shape[1]} aligned ordinary segments', flush=True)
    result = dict(repository=REPOSITORY, pinned_commit=COMMIT,
        outcome='One iff all retained ordinary raters report no minor/major/critical translation error for that segment',
        estimand='Unweighted finite mean of derived exact binary consensus scores on the fixed common annotated pool',
        scope='Recorded annotation consensus, not severity-weighted MQM or latent true human quality',
        parser='Literal tab splitting; exact known header/comment; reject unknown severities or malformed rows',
        exclusions='References/human outputs and segments with any HOTW-test/canary annotation; source issues and neutral opinions are not errors',
        source_license='Upstream Apache-2.0; copied LICENSE supplied', datasets=records)
    (output_directory / 'DATA_PROVENANCE.json').write_text(json.dumps(result, indent=2))
    return result

def load_data(directory):
    directory = Path(directory)
    provenance = json.loads((directory / 'DATA_PROVENANCE.json').read_text())
    result = {}
    for record in provenance['datasets']:
        pair = record['language_pair']
        with np.load(directory / f'wmt23_{pair}_error_free.npz', allow_pickle=False) as z:
            scores, names, items = z['scores'], z['systems'], z['items']
        if matrix_hash(scores, names, items) != record['matrix_sha256']:
            raise ValueError(f'Derived matrix checksum failed: {pair}')
        if np.any((scores != 0) & (scores != 1)):
            raise ValueError('Nonbinary public outcomes')
        result[pair] = (scores, names, items)
    return result, provenance

def leave_one_out(scores, names, target):
    target_rows = np.flatnonzero(np.asarray(names) == target)
    if len(target_rows) != 1:
        raise ValueError('Unknown or nonunique target')
    keep = np.asarray(names) != target
    return np.asarray(scores)[keep].copy(), np.asarray(names)[keep].copy(), int(target_rows[0])

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--raw-directory', default='raw_downloads')
    p.add_argument('--output', default='data')
    p.add_argument('--download', action='store_true')
    args = p.parse_args()
    prepare(args.raw_directory, args.output, args.download)
