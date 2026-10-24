"""End-to-end packet and response handoff checks with artificial judgments."""
import csv
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from build_collection_kit import make_kit
from combine_responses import COLUMNS, combine


class CollectionKitTests(unittest.TestCase):
    def test_distinct_blinded_rater_packets_and_complete_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            items = root / "items.csv"
            with items.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=[
                    "item_id", "source", "reference", *"ABCDEFGH"])
                writer.writeheader()
                for i in range(40):
                    writer.writerow({"item_id": f"doc{i}",
                                     "source": f"<script>source{i}</script>",
                                     "reference": "参考", **{
                                         s: f"候选{i}-{s}" for s in "ABCDEFGH"}})
            (root / "raters.csv").write_text("rater_id\nR01\nR02\nR03\nR04\n")
            folder = root / "kit"
            manifest = make_kit(items, root / "raters.csv", folder,
                                validate_frozen=False)
            self.assertEqual(manifest["tasks"], 160)
            self.assertEqual(manifest["rater_task_counts"], {
                f"R{i:02}": 40 for i in range(1, 5)})
            with zipfile.ZipFile(folder.with_suffix(".zip")) as z:
                self.assertEqual(len(z.namelist()), 10)
            with (folder / "researcher_only/private_key.csv").open() as stream:
                key = list(csv.DictReader(stream))
            self.assertEqual(len(key), 160)
            for i in range(40):
                block = [r for r in key if r["item_id"] == f"doc{i}"]
                self.assertEqual(len({r["rater_id"] for r in block}), 4)
                self.assertEqual([r["context"] for r in block].count("P0"), 2)
            template = folder / "researcher_only/responses_template.csv"
            with template.open() as stream:
                expected = list(csv.DictReader(stream))
            response_files = []
            for j in range(1, 5):
                rater = f"R{j:02}"
                page = (folder / "rater_packets" / f"{rater}.html").read_text()
                self.assertNotIn("<script>source", page)
                payload = re.search(r'<script id="tasks" type="application/json">(.*?)</script>',
                                    page, re.S).group(1)
                visible = json.loads(payload)
                self.assertEqual(len(visible), 40)
                self.assertEqual([r["task_order"] for r in visible], list(range(1, 41)))
                self.assertEqual({r["rater_id"] for r in visible}, {rater})
                self.assertTrue(all("context" not in r and "slot_1" not in r
                                    and "item_id" not in r for r in visible))
                responses = [{**r, **{f"rank_{k}": str(k) for k in range(1, 6)},
                              "seconds": "10.00"} for r in expected
                             if r["rater_id"] == rater]
                path = root / f"{rater}_synthetic.csv"
                with path.open("w", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=COLUMNS)
                    writer.writeheader()
                    writer.writerows(responses)
                response_files.append(path)
            combined = root / "combined.csv"
            self.assertEqual(combine(template, response_files, combined), 160)
            with combined.open() as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 160)
            combined.unlink()
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                combine(template, response_files + response_files[:1], combined)
            self.assertFalse(combined.exists())
            with self.assertRaisesRegex(ValueError, "Missing"):
                combine(template, response_files[:-1], combined)
            self.assertFalse(combined.exists())

    def test_no_regeneration_over_existing_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            items = root / "items.csv"
            with items.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=[
                    "item_id", "source", "reference", *"ABCDEFGH"])
                writer.writeheader()
                for i in range(40):
                    writer.writerow({"item_id": str(i), "source": f"source {i}",
                                     "reference": f"ref {i}", **{
                                         s: f"translation {s} {i}" for s in "ABCDEFGH"}})
            (root / "raters.csv").write_text("rater_id\nR01\nR02\nR03\nR04\n")
            folder = root / "kit"
            folder.mkdir()
            (folder / "existing.txt").write_text("do not overwrite")
            with self.assertRaisesRegex(ValueError, "new or empty output"):
                make_kit(items, root / "raters.csv", folder, validate_frozen=False)
            self.assertEqual((folder / "existing.txt").read_text(), "do not overwrite")


if __name__ == "__main__":
    unittest.main()
