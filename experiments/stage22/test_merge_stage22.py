import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from merge_stage22 import merge


class MergeInvariants(unittest.TestCase):
    def _shard(self, root, language):
        path = root / language
        path.mkdir()
        metadata = dict(
            master=1, repeats=1, languages=[language], include_diagnostics=True,
            methods=["star_common", "star_pruned"], fractions=[.25, .5, .75],
            protocol_sha256="p", source_sha256="s",
            matrix_hashes={language: "m"}, systems={language: 3},
            task_counts={language: 1},
        )
        (path / "metadata.json").write_text(json.dumps(metadata))
        comparison = dict(language=language, repeat="0", graph="star",
                          task_id="reference:0", value="1.25")
        with (path / "comparison.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=comparison.keys())
            writer.writeheader(); writer.writerow(comparison)
        checkpoint = dict(language=language, repeat="0", graph="star",
                          task_id="reference:0", method="star_common",
                          fraction="0.25", value="7")
        with (path / "checkpoints.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=checkpoint.keys())
            writer.writeheader(); writer.writerow(checkpoint)
        return path

    def test_disjoint_shards_merge_without_value_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self._shard(root, "a")
            second = self._shard(root, "b")
            rows, checkpoints, metadata = merge([first, second], root / "merged")
            self.assertEqual([row["value"] for row in rows], ["1.25", "1.25"])
            self.assertEqual([row["value"] for row in checkpoints], ["7", "7"])
            self.assertEqual(metadata["languages"], ["a", "b"])

    def test_overlapping_languages_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self._shard(root, "a")
            copied = root / "copy"
            copied.mkdir()
            for name in ("metadata.json", "comparison.csv", "checkpoints.csv"):
                (copied / name).write_bytes((first / name).read_bytes())
            with self.assertRaises(ValueError):
                merge([first, copied], root / "merged")


if __name__ == "__main__":
    unittest.main()
