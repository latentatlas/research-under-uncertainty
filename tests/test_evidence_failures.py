"""Meaningful corruption checks; no model or network calls."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import replay


class EvidenceFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.data = replay.read(cls.root / "data/episodes.json")
        cls.rubric = replay.read(cls.root / "src/RUBRIC.json")

    def inputs(self, index):
        episode = deepcopy(self.data["episodes"][index])
        folder = self.root / "evidence" / episode["id"]
        return [episode, replay.read(folder / "PACKETS.json"), replay.read(folder / "REVIEW.json"),
                replay.read(folder / "PROFILE.json"), self.rubric]

    def test_changed_measurement_fails_even_without_file_hash_check(self):
        args = self.inputs(0)
        args[0]["observations"][0]["values"][0] = "42.000000"
        with self.assertRaisesRegex(replay.EvidenceError, "observation disagrees"):
            replay.validate_episode(*args)

    def test_missing_submission_cannot_be_relabelled_as_zero_score(self):
        args = self.inputs(1)
        args[0]["original_accepted"] = [False] * 24
        with self.assertRaisesRegex(replay.EvidenceError, "must stay unscored"):
            replay.validate_episode(*args)

    def test_rating_citation_cannot_point_to_changed_evidence(self):
        args = self.inputs(0)
        ref = args[2]["decisions"][0]["dimensions"]["D2"]["evidence"][0]
        ref["value_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "pointer/hash differs"):
            replay.validate_episode(*args)

    def test_missing_evidence_file_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data/MANIFEST.json").write_text('{"files":[{"path":"missing.json","sha256":"missing"}]}')
            with self.assertRaisesRegex(replay.EvidenceError, "Missing evidence"):
                replay.check_inventory(root)


if __name__ == "__main__":
    unittest.main()
