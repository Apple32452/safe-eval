"""Prepare a development-only English-to-Chinese panel pilot from public WMT25."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


LANGUAGE = "en-zh_CN"
SEED = 3303
SYSTEMS = {
    "A": "Qwen3-235B", "B": "GPT-4.1",
    "C": "Algharb", "D": "Shy", "E": "Claude-4",
    "F": "IRB-MT", "G": "RuZh", "H": "Laniqo",
}
SOURCE_BYTES = 128674273
SOURCE_SHA256 = "a36ebce10c9ea26f71449933721de3a87e27f6a5b09d96b5daa026eaf1d197ab"


def eligible_rows(rows: Iterable[dict]) -> dict[str, list[dict]]:
    by_doc = defaultdict(list)
    for row in rows:
        doc_id = row.get("doc_id", "")
        if not doc_id.startswith(LANGUAGE + "_#_") or len(doc_id.split("_#_")) < 4:
            continue
        translations = row.get("tgt_text")
        if not isinstance(translations, dict) or not isinstance(row.get("src_text"), str):
            continue
        choices = [translations.get(s) for s in SYSTEMS.values()]
        reference = translations.get("refA")
        if (not all(isinstance(x, str) and x.strip() for x in choices) or
                len({x.strip() for x in choices}) != 8 or
                not isinstance(reference, str) or not reference.strip() or
                not row["src_text"].strip()):
            continue
        document = "_#_".join(doc_id.split("_#_")[:-1])
        by_doc[document].append({
            "item_id": doc_id, "source": row["src_text"],
            "reference": reference,
            **{letter: translations[system] for letter, system in SYSTEMS.items()},
        })
    return by_doc


def select(by_doc: dict[str, list[dict]], count: int = 40,
           seed: int = SEED) -> list[dict]:
    if count < 1 or len(by_doc) < count:
        raise ValueError("not enough distinct documents with complete translations")
    rng = np.random.default_rng(seed)
    docs = rng.permutation(sorted(by_doc))
    selected = [by_doc[str(doc)][int(rng.integers(len(by_doc[str(doc)])))]
                for doc in docs[:count]]
    return selected


def extract(source: Path, output: Path, count: int = 40) -> dict:
    if source.stat().st_size != SOURCE_BYTES:
        raise ValueError("WMT25 source size does not match the documented public release")
    digest_state = hashlib.sha256()

    def verified_rows():
        with source.open("rb") as stream:
            for raw in stream:
                digest_state.update(raw)
                if raw.strip():
                    yield json.loads(raw)

    by_doc = eligible_rows(verified_rows())
    digest = digest_state.hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError("WMT25 source hash mismatch")
    selected = select(by_doc, count)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "candidate_items.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "item_id", "source", "reference", *SYSTEMS])
        writer.writeheader()
        writer.writerows(selected)
    item_digest = hashlib.sha256(
        json.dumps([r["item_id"] for r in selected], ensure_ascii=False).encode()
    ).hexdigest()
    manifest = {
        "dataset": "WMT25 public General MT human evaluation text, development only",
        "source_sha256": digest, "language": LANGUAGE, "seed": SEED,
        "eligible_documents": len(by_doc), "selected_documents": len(selected),
        "selected_item_ids_sha256": item_digest, "system_mapping": SYSTEMS,
        "selection": "seeded sample of documents; one eligible segment per document",
        "disclosure": "systems selected using existing WMT25 mean scores before new human pilot",
    }
    (output / "candidate_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--count", type=int, default=40)
    args = parser.parse_args()
    print(json.dumps(extract(args.source, args.output, args.count), indent=2))
