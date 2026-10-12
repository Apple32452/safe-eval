"""Check that the Stage 7 files still match their released SHA256 manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1] / 'experiments' / 'stage7'
    manifest = json.loads((root / 'MANIFEST_SHA256.json').read_text())
    failures = []
    for relative, expected in manifest.items():
        path = (root / relative).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            failures.append(relative + ': path outside the released directory')
            continue
        if not path.is_file():
            failures.append(relative + ': missing')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(relative + ': SHA256 differs')
    if failures:
        print('\n'.join(failures), file=sys.stderr)
        return 1
    print(f'Verified {len(manifest)} released Stage 7 file hashes.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
