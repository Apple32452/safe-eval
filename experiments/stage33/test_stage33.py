"""Checks for complete panels, independent rater allocation and paired signs."""
import csv
import tempfile
import unittest
from pathlib import Path

from analyze_human_pilot import analyze
from audit_legacy_panels import audit, interval
from extract_wmt25_candidates import eligible_rows, select
from prepare_human_pilot import build, read_items


def example(item_id):
    return {"item_id": item_id, "source": "source " + item_id,
            "reference": "reference " + item_id,
            **{x: f"translation {x} {item_id}" for x in "ABCDEFGH"}}


class Stage33Invariants(unittest.TestCase):
    def test_blind_allocation_one_rater_per_input(self):
        items = [example("one"), example("two")]
        raters = [f"r{k}" for k in range(6)]
        tasks, key = build(items, raters, 2)
        self.assertEqual((tasks, key), build(items, raters, 2))
        self.assertEqual(len(tasks), 8)
        for item in ("one", "two"):
            self.assertEqual(len({k["rater_id"] for k in key if k["item_id"] == item}), 4)
            self.assertEqual({k["context"] for k in key if k["item_id"] == item},
                             {"P0", "P1"})
        for task, k in zip(tasks, key):
            self.assertEqual(len({task[f"option_{i}"] for i in range(1, 6)}), 5)
            self.assertEqual({k[f"slot_{i}"] for i in range(1, 6)},
                             set(("A", "B", "C", "D", "E") if
                                 k["context"] == "P0" else ("A", "B", "F", "G", "H")))
        with self.assertRaises(ValueError):
            build(items, raters[:3], 2)

    def test_paired_human_sign_and_validation(self):
        _, key = build([example("one"), example("two")], [f"r{k}" for k in range(4)], 2)
        responses = []
        for k in key:
            slots = [k[f"slot_{i}"] for i in range(1, 6)]
            order = (["A", "B"] if k["context"] == "P0" else ["B", "A"])
            order.extend(s for s in slots if s not in ("A", "B"))
            responses.append({"task_id": k["task_id"], "rater_id": k["rater_id"],
                              **{f"rank_{i}": str(order.index(s) + 1)
                                 for i, s in enumerate(slots, 1)},
                              "seconds": "10" if k["context"] == "P0" else "20"})
        result = analyze(key, responses, draws=100)
        self.assertEqual(result["effect"]["mean"], -2.)
        self.assertEqual(result["effect"]["cluster_bootstrap_95"], [-2., -2.])
        self.assertEqual(result["mean_task_seconds"], {"P0": 10., "P1": 20.})
        with self.assertRaises(ValueError):
            analyze(key, responses[:-1])
        bad = [dict(r) for r in responses]
        bad[0]["rank_1"] = "0"
        with self.assertRaises(ValueError):
            analyze(key, bad)

    def test_legacy_requires_complete_five_way_and_detects_cross_panel(self):
        header = ["srclang", "trglang", "srcIndex", "judgeId"]
        header += [f"system{i}Id" for i in range(1, 6)]
        header += [f"system{i}rank" for i in range(1, 6)]
        records = [
            ["X", "Y", "1", "r1", "A", "B", "C", "D", "_ref", 1, 2, 3, 4, 5],
            ["X", "Y", "1", "r2", "A", "B", "C", "D", "F", 2, 1, 3, 4, 5],
            ["X", "Y", "2", "r3", "A", "B", "C", "D", "blank", 1, 2, 3, 4, -1],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "wmt.csv"
            with p.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                writer.writerows(records)
            result = audit(p, draws=100)
        self.assertEqual(result["rankings"], 3)
        self.assertEqual(result["complete_five_way"], 2)
        self.assertEqual(result["different_companion_panel_pair_items"], 6)
        self.assertEqual(result["opposite_nontied_signs_across_panels"], 1)
        self.assertEqual(result["reference_presence_disjoint_raters"]["pair_items"], 6)

    def test_cluster_bootstrap_resamples_inputs_together(self):
        cells = [(("x", "y", "1"), 1.), (("x", "y", "1"), 1.),
                 (("x", "y", "2"), -1.)]
        result = interval(cells, seed=2, draws=200)
        self.assertEqual(result["source_items"], 2)
        self.assertAlmostEqual(result["mean"], 1 / 3)

    def test_template_rejects_duplicate_system_outputs(self):
        item = example("one")
        item["B"] = item["A"]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "items.csv"
            with p.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(item))
                writer.writeheader()
                writer.writerow(item)
            with self.assertRaises(ValueError):
                read_items(p)

    def test_one_segment_per_document_selection(self):
        systems = ("Qwen3-235B", "GPT-4.1", "Algharb", "Shy",
                   "Claude-4", "IRB-MT", "RuZh", "Laniqo")
        rows = []
        for doc in ("doc1", "doc2"):
            for segment in range(2):
                rows.append({
                    "doc_id": f"en-zh_CN_#_news_#_{doc}_#_{segment}",
                    "src_text": f"English {doc} {segment}",
                    "tgt_text": {"refA": "reference",
                                 **{s: f"Chinese {s} {doc} {segment}"
                                    for s in systems}},
                })
        grouped = eligible_rows(rows)
        self.assertEqual(len(grouped), 2)
        selected = select(grouped, count=2)
        self.assertEqual(len({r["item_id"].rsplit("_#_", 1)[0]
                              for r in selected}), 2)
        self.assertEqual(selected, select(grouped, count=2))


if __name__ == "__main__":
    unittest.main()
