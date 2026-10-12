"""Pinned public WMT24 annotations -> bounded, aligned human-score matrices.

This is a DERIVED error-free indicator, not the official severity-weighted MQM
score. Files are literal TSV: quoting="QUOTE_NONE" behavior is intentional.
The distributed numeric extracts make the experiment work without a download.
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
    'en-de': ('generalMT2024/mqm_generalMT2024_ende.tsv',
              '4ae6c64ea3aad4a5286bf70c19c61c9d39ef2cc2da68637b26f1f91454498c20'),
    'en-es': ('generalMT2024/mqm_generalMT2024_enes.tsv',
              '9e29aa0af6f8367ab615d6ad363145ad66a036d09decd301ec2a27827f3fa9d3'),
    'ja-zh': ('generalMT2024/mqm_generalMT2024_jazh.tsv',
              'be17442ffd919859e17e1f8c5cdd2110d5f9e27e8e4c24ba3e902ba1febe0a7b'),
}
HEADER = ['system', 'doc', 'docSegId', 'globalSegId', 'rater', 'source',
          'target', 'category', 'severity', 'metadata']
ERROR_SEVERITIES = {'minor', 'major', 'critical'}
KNOWN_SEVERITIES = ERROR_SEVERITIES | {'no-error', 'neutral'}


def source_issue(category):
    return category.strip().casefold().replace('_', ' ') == 'source issue'


def parse_annotations(text):
    """Fail on malformed/unknown records; never silently fill missing outcomes.

    Return all named systems before reference filtering. Each segment/rater is
    scored 1 iff it has no minor/major/critical translation-error annotations.
    Source-issue annotations and neutral opinions do not count as errors.
    """
    lines = text.splitlines()
    if not lines or lines[0].split('\t') != HEADER:
        raise ValueError('Unexpected WMT TSV header')
    errors = defaultdict(bool)
    canary_units = set()
    severity_counts = Counter()
    source_rows = neutral_rows = record_count = 0
    for line_number, line in enumerate(lines[1:], 2):
        if not line:
            continue
        fields = line.split('\t')
        if len(fields) != len(HEADER):
            raise ValueError(f'Line {line_number}: expected 10 literal tab fields')
        system, doc, docseg, globalseg, rater, src, _, category, severity, _ = fields
        if not all((system, doc, rater)) or not docseg.isdigit() or not globalseg.isdigit():
            raise ValueError(f'Line {line_number}: invalid item identity')
        sev = severity.strip().casefold()
        if sev not in KNOWN_SEVERITIES:
            raise ValueError(f'Line {line_number}: unknown severity {severity!r}')
        severity_counts[severity] += 1
        record_count += 1
        item = (doc, int(docseg), int(globalseg))
        if doc.casefold() == 'canary' or src.startswith('CANARY GUID'):
            canary_units.add(item)
            continue
        key = (system, item, rater)
        errors[key] = errors[key]  # Preserve an observed no-error/source-only rating.
        source_rows += int(source_issue(category))
        neutral_rows += int(sev == 'neutral')
        if not source_issue(category) and sev in ERROR_SEVERITIES:
            errors[key] = True
    raters = defaultdict(list)
    for (system, item, rater), has_error in errors.items():
        raters[(system, item)].append((rater, 1.0 - float(has_error)))
    systems = defaultdict(dict)
    for (system, item), ratings in raters.items():
        systems[system][item] = float(np.mean([value for _, value in ratings]))
    audit = dict(annotation_rows=record_count,
                 severity_counts=dict(sorted(severity_counts.items())),
                 excluded_canary_items=len(canary_units),
                 ignored_source_issue_rows=source_rows, ignored_neutral_rows=neutral_rows,
                 raters_per_system_item=dict(sorted(Counter(len(v) for v in raters.values()).items())))
    return dict(systems), audit


def make_matrix(systems):
    references = sorted(s for s in systems if s.casefold().startswith(('ref', 'human')))
    mt = {s: v for s, v in systems.items() if s not in references}
    if len(mt) < 3:
        raise ValueError('Need at least three translation systems')
    common = set.intersection(*(set(v) for v in mt.values()))
    if not common:
        raise ValueError('No commonly annotated items')
    items = sorted(common, key=lambda k: (k[2], k[0], k[1]))
    global_ids = [i[2] for i in items]
    if len(set(global_ids)) != len(items):
        raise ValueError('Global segment IDs do not uniquely identify common items')
    names = sorted(mt)
    matrix = np.array([[mt[s][i] for i in items] for s in names], dtype=float)
    audit = dict(translation_systems=len(names), excluded_references=references,
                 common_items=len(items), system_names=names,
                 observed_items_per_system={s: len(mt[s]) for s in names},
                 removed_noncommon_items_per_system={s: len(mt[s]) - len(items) for s in names})
    return matrix, np.array(names), np.array(items, dtype=str), audit


def matrix_hash(matrix, names, items):
    h = hashlib.sha256(np.asarray(matrix, dtype='<f8').tobytes())
    h.update(json.dumps(names.tolist(), ensure_ascii=False, separators=(',', ':')).encode())
    h.update(json.dumps(items.tolist(), ensure_ascii=False, separators=(',', ':')).encode())
    return h.hexdigest()


def prepare(raw_directory, output_directory, download=False):
    raw_directory, output_directory = Path(raw_directory), Path(output_directory)
    raw_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    datasets = []
    for pair, (relative, expected) in SOURCES.items():
        path = raw_directory / Path(relative).name
        url = f'https://raw.githubusercontent.com/google/wmt-mqm-human-evaluation/{COMMIT}/{relative}'
        if download:
            with urllib.request.urlopen(url, timeout=90) as response:
                path.write_bytes(response.read())
        if not path.exists():
            raise FileNotFoundError(f'{path}; use --download to fetch pinned originals')
        payload = path.read_bytes()
        observed = hashlib.sha256(payload).hexdigest()
        if observed != expected:
            raise ValueError(f'Source checksum mismatch: {path}')
        systems, audit = parse_annotations(payload.decode('utf-8'))
        matrix, names, items, aligned = make_matrix(systems)
        np.savez_compressed(output_directory / f'wmt24_{pair}_error_free.npz',
                            scores=matrix, systems=names, items=items)
        datasets.append(dict(language_pair=pair, source_url=url, source_sha256=observed,
                             source_bytes=len(payload), matrix_sha256=matrix_hash(matrix, names, items),
                             **audit, **aligned))
        print(f'{pair}: {len(names)} MT systems x {matrix.shape[1]} aligned segments', flush=True)
    record = dict(repository=REPOSITORY, pinned_commit=COMMIT,
                  source_license='Upstream repository LICENSE: Apache-2.0; copy in UPSTREAM_LICENSE.txt',
                  outcome='Mean of per-rater indicators of no reported minor/major/critical translation errors',
                  exclusions='Reference/human outputs, canary items; source issues and neutral opinions are not translation errors',
                  parser='Literal tab splitting; no CSV quote interpretation; reject malformed/unknown records',
                  estimand='Unweighted finite mean on commonly annotated segments in this release, separately for each system and language pair',
                  scope='Derived binary human outcome, not the official severity-weighted MQM score or corpus BLEU',
                  datasets=datasets)
    (output_directory / 'DATA_PROVENANCE.json').write_text(json.dumps(record, indent=2))
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-directory', default='raw_downloads')
    parser.add_argument('--output', default='data')
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    prepare(args.raw_directory, args.output, args.download)
