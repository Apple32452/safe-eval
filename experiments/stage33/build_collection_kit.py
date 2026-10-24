"""Create private, offline Stage 33 rater packets from the frozen assignment."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path

from prepare_human_pilot import SEED, build, read_items, read_raters, write_csv


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "rater_template.html"
SAFE_ID = re.compile(r"[A-Za-z0-9_-]+\Z")
EXPECTED_CSV_SHA256 = "b154fa7bfb500bdc6cd1cb9f05c17ff3a6ccb6950901c6b6708175b884728216"
EXPECTED_IDS_SHA256 = "08a5451563a6b292c5467e9dc2d4cf2fe52f691351c277d7766fec447fa7f06c"
RESPONSE_COLUMNS = ["task_id", "rater_id", "task_order",
                    *[f"rank_{i}" for i in range(1, 6)], "seconds"]


def make_kit(items_path: Path, raters_path: Path, output: Path,
             repeats: int = 2, validate_frozen: bool = True) -> dict:
    items, raters = read_items(items_path), read_raters(raters_path)
    candidate_hash = hashlib.sha256(items_path.read_bytes()).hexdigest()
    item_hash = hashlib.sha256(json.dumps([item["item_id"] for item in items],
                                          ensure_ascii=False).encode()).hexdigest()
    if validate_frozen and (candidate_hash != EXPECTED_CSV_SHA256 or
                            item_hash != EXPECTED_IDS_SHA256):
        raise ValueError("Candidate items differ from the frozen WMT25 pilot extract")
    if len(items) != 40 or repeats != 2 or len(raters) < 4:
        raise ValueError("Frozen pilot requires 40 items, two judges per context, >=4 judges")
    if any(not SAFE_ID.fullmatch(rater) for rater in raters):
        raise ValueError("Use pseudonymous rater IDs with letters, digits, _ or - only")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Choose a new or empty output directory; old assignments cannot be reused")
    archive = output.with_suffix(".zip")
    if archive.exists():
        raise ValueError("Archive already exists; choose a new output name")
    tasks, key = build(items, raters, repeats)
    ordered = sorted(tasks, key=lambda t: (t["rater_id"], t["task_order"]))
    by_rater = Counter(t["rater_id"] for t in ordered)
    if len(tasks) != 160 or any(len({k["rater_id"] for k in key
                                      if k["item_id"] == item["item_id"]}) != 4
                                for item in items):
        raise AssertionError("Pilot assignment is incomplete")

    rater_dir = output / "rater_packets"
    private_dir = output / "researcher_only"
    rater_dir.mkdir(parents=True)
    private_dir.mkdir()
    template = TEMPLATE.read_text(encoding="utf-8")
    for rater in raters:
        visible = [{field: t[field] for field in
                    ("task_id", "rater_id", "task_order", "source", "reference",
                     *[f"option_{i}" for i in range(1, 6)])}
                   for t in ordered if t["rater_id"] == rater]
        payload = json.dumps(visible, ensure_ascii=False).replace("<", "\\u003c")
        version = hashlib.sha256("|".join(t["task_id"] for t in visible).encode()).hexdigest()[:16]
        page = (template.replace("__RATER_ID__", rater)
                        .replace("__PACKET_VERSION__", version)
                        .replace("__TASKS_JSON__", payload))
        (rater_dir / f"{rater}.html").write_text(page, encoding="utf-8")

    write_csv(private_dir / "private_key.csv", key,
              ["task_id", "item_id", "rater_id", "task_order", "context",
               *[f"slot_{i}" for i in range(1, 6)]])
    write_csv(private_dir / "responses_template.csv",
              [{"task_id": t["task_id"], "rater_id": t["rater_id"],
                "task_order": t["task_order"],
                **{f"rank_{i}": "" for i in range(1, 6)}, "seconds": ""}
               for t in ordered], RESPONSE_COLUMNS)
    (private_dir / "raters.csv").write_text(
        "rater_id\n" + "".join(r + "\n" for r in raters), encoding="utf-8")
    manifest = {"study": "Stage 33 WMT25 development feasibility pilot",
                "items": len(items), "tasks": len(tasks), "rater_task_counts": dict(by_rater),
                "assignment_seed": SEED, "repeats_per_context": repeats,
                "candidate_csv_sha256": candidate_hash,
                "selected_item_ids_sha256": item_hash,
                "status": "NO HUMAN RESPONSES; collection packet only"}
    (private_dir / "collection_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(ROOT / "combine_responses.py", private_dir / "combine_responses.py")
    (output / "START_HERE.txt").write_text(
        "SAFE-EVAL Stage 33: 40 items, 160 five-way ranking tasks.\n\n"
        "Recruit four distinct English-Chinese bilingual volunteers and follow your "
        "institution's ethics/consent rules.\n"
        "Privately map each volunteer to one pseudonym (R01, R02, R03, R04); "
        "retain the mapping outside this packet.\n"
        "Give each volunteer ONLY their own rater_packets/<ID>.html file. "
        "Do not send the whole archive or researcher_only directory.\n"
        "The offline page shows English source, Chinese reference, and five "
        "anonymous candidate translations.\n"
        "They assign ranks 1 (best) to 5 (worst), allowing ties, and download "
        "one <ID>_responses.csv at the end.\n"
        "The page records active task time, pauses on tab hide, and stores "
        "progress locally in that browser until CSV download. No server upload.\n"
        "Keep the returned CSVs, private key, and identity mapping private; "
        "do not commit them to public GitHub.\n"
        "Collect four CSVs in a private folder named responses/, then run:\n"
        "  python researcher_only/combine_responses.py "
        "--template researcher_only/responses_template.csv "
        "--responses responses/*.csv --output researcher_only/responses.csv\n"
        "From the SAFE-EVAL repository root, run the Stage 33 descriptive "
        "and Stage 34 exact analyses as documented in their READMEs.\n"
        "Before analysis, log consent, actual task-order deviations, "
        "interruptions, exclusions, and any missing tasks.\n"
        "If somebody has received a packet, never regenerate the assignment "
        "or silently edit their file.\n",
        encoding="utf-8")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                z.write(path, path.relative_to(output))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True, type=Path)
    parser.add_argument("--raters", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(make_kit(args.items, args.raters, args.output), indent=2))
