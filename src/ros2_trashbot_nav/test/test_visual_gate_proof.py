import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
import sys
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_nav.visual_gate_proof import build_visual_gate_proof, main


class StubMatcher:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def __call__(self, keyframe_path, live_frame_path, threshold):
        self.calls.append((str(keyframe_path), str(live_frame_path), threshold))
        if self.results:
            return self.results.pop(0)
        return "passed", 99, "stub matched"


def write_route(path):
    path.write_text(
        "waypoints:\n"
        "  - frame_id: map\n"
        "    x: 1.0\n"
        "    y: 2.0\n"
        "    qw: 1.0\n"
        "  - frame_id: map\n"
        "    x: 3.0\n"
        "    y: 4.0\n"
        "    qw: 1.0\n",
        encoding="utf-8",
    )


def write_csv_route(path):
    path.write_text(
        "frame_id,x,y,z,qx,qy,qz,qw\n"
        "map,1.0,2.0,0.0,0.0,0.0,0.0,1.0\n",
        encoding="utf-8",
    )


def touch_frames(directory, indexes):
    directory.mkdir(parents=True, exist_ok=True)
    for index in indexes:
        (directory / f"{index:03d}.jpg").write_bytes(b"fixture")


class VisualGateProofTest(unittest.TestCase):
    def test_passed_proof_artifact_contains_debug_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = root / "fixed_route.yaml"
            keyframes = root / "keyframes"
            live_frames = root / "live"
            write_route(route)
            touch_frames(keyframes, [0, 1])
            touch_frames(live_frames, [0, 1])

            proof = build_visual_gate_proof(
                str(route),
                str(keyframes),
                str(live_frames),
                threshold=25,
                matcher=StubMatcher([
                    ("passed", 32, "stub matched"),
                    ("passed", 26, "stub matched"),
                ]),
            )

            self.assertEqual(proof["route"]["contract_version"], "fixed_route.v1")
            self.assertEqual(proof["route"]["total_checkpoints"], 2)
            self.assertEqual(proof["summary"]["status"], "passed")
            self.assertEqual(proof["summary"]["passed"], 2)
            self.assertEqual(proof["summary"]["failed"], 0)
            self.assertEqual(proof["route_proof_summary"]["coverage_rate"], 1.0)
            self.assertEqual(proof["route_proof_summary"]["covered_checkpoints"], 2)
            self.assertEqual(proof["route_proof_summary"]["total_checkpoints"], 2)
            self.assertEqual(proof["route_proof_summary"]["missing_checkpoints"], [])
            self.assertEqual(proof["route_proof_summary"]["gate_status"], "passed")
            self.assertEqual(proof["route_proof_summary"]["last_block_reason"], "")
            self.assertEqual(proof["checkpoints"][0]["status"], "passed")
            self.assertEqual(proof["checkpoints"][0]["match_count"], 32)
            self.assertEqual(proof["checkpoints"][0]["threshold"], 25)
            self.assertEqual(proof["debug_status"]["visual_gate_status"], "passed")
            self.assertEqual(proof["debug_status"]["visual_gate_checkpoint"], 1)
            self.assertEqual(proof["debug_status"]["failure_reason"], "")
            self.assertTrue(proof["debug_status"]["keyframe_preflight"]["route_visual_ready"])

    def test_csv_route_and_dict_matcher_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = root / "fixed_route.csv"
            keyframes = root / "keyframes"
            live_frames = root / "live"
            write_csv_route(route)
            touch_frames(keyframes, [0])
            touch_frames(live_frames, [0])

            proof = build_visual_gate_proof(
                str(route),
                str(keyframes),
                str(live_frames),
                threshold=25,
                matcher=StubMatcher([
                    {"status": "passed", "match_count": 40, "detail": "dict matched"},
                ]),
            )

            self.assertEqual(proof["summary"]["status"], "passed")
            self.assertEqual(proof["route"]["total_checkpoints"], 1)
            self.assertEqual(proof["checkpoints"][0]["match_count"], 40)
            self.assertEqual(proof["route_proof_summary"]["coverage_rate"], 1.0)
            self.assertEqual(proof["route_proof_summary"]["covered_checkpoints"], 1)
            self.assertEqual(proof["route_proof_summary"]["total_checkpoints"], 1)
            self.assertEqual(proof["route_proof_summary"]["missing_checkpoints"], [])
            self.assertEqual(proof["route_proof_summary"]["gate_status"], "passed")

    def test_insufficient_matches_is_structured_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = root / "fixed_route.yaml"
            keyframes = root / "keyframes"
            live_frames = root / "live"
            write_route(route)
            touch_frames(keyframes, [0, 1])
            touch_frames(live_frames, [0, 1])

            proof = build_visual_gate_proof(
                str(route),
                str(keyframes),
                str(live_frames),
                threshold=25,
                matcher=StubMatcher([
                    ("passed", 12, "stub matched"),
                    ("passed", 30, "stub matched"),
                ]),
            )

            self.assertEqual(proof["summary"]["status"], "failed")
            self.assertEqual(proof["summary"]["failed"], 1)
            self.assertEqual(proof["summary"]["failure_reasons"], {"insufficient_matches": 1})
            self.assertEqual(proof["checkpoints"][0]["status"], "insufficient_matches")
            self.assertIn("12/25", proof["checkpoints"][0]["detail"])
            self.assertEqual(proof["route_proof_summary"]["coverage_rate"], 0.0)
            self.assertEqual(proof["route_proof_summary"]["covered_checkpoints"], 0)
            self.assertEqual(proof["route_proof_summary"]["total_checkpoints"], 2)
            self.assertEqual(proof["route_proof_summary"]["missing_checkpoints"], [0, 1])
            self.assertEqual(proof["route_proof_summary"]["gate_status"], "insufficient_matches")
            self.assertIn("12/25", proof["route_proof_summary"]["last_block_reason"])
            self.assertEqual(proof["debug_status"]["visual_gate_status"], "insufficient_matches")
            self.assertEqual(proof["debug_status"]["visual_gate_checkpoint"], 0)

    def test_missing_keyframe_is_reported_before_matching(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = root / "fixed_route.yaml"
            keyframes = root / "keyframes"
            live_frames = root / "live"
            write_route(route)
            touch_frames(keyframes, [1])
            touch_frames(live_frames, [0, 1])
            matcher = StubMatcher([("passed", 30, "stub matched")])

            proof = build_visual_gate_proof(
                str(route),
                str(keyframes),
                str(live_frames),
                threshold=25,
                matcher=matcher,
            )

            self.assertEqual(proof["checkpoints"][0]["status"], "missing_keyframe")
            self.assertEqual(proof["summary"]["failure_reasons"], {"missing_keyframe": 1})
            self.assertEqual(proof["route_proof_summary"]["coverage_rate"], 0.0)
            self.assertEqual(proof["route_proof_summary"]["covered_checkpoints"], 0)
            self.assertEqual(proof["route_proof_summary"]["total_checkpoints"], 2)
            self.assertEqual(proof["route_proof_summary"]["missing_checkpoints"], [0, 1])
            self.assertEqual(proof["route_proof_summary"]["gate_status"], "missing_keyframe")
            self.assertIn("missing keyframe", proof["route_proof_summary"]["last_block_reason"])
            self.assertEqual(proof["debug_status"]["keyframe_preflight"]["missing_keyframes"], [0])
            self.assertEqual(len(matcher.calls), 1)

    def test_missing_live_frame_is_reported_before_matching(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = root / "fixed_route.yaml"
            keyframes = root / "keyframes"
            live_frames = root / "live"
            write_route(route)
            touch_frames(keyframes, [0, 1])
            touch_frames(live_frames, [1])
            matcher = StubMatcher([("passed", 30, "stub matched")])

            proof = build_visual_gate_proof(
                str(route),
                str(keyframes),
                str(live_frames),
                threshold=25,
                matcher=matcher,
            )

            self.assertEqual(proof["checkpoints"][0]["status"], "missing_live_frame")
            self.assertEqual(proof["summary"]["failure_reasons"], {"missing_live_frame": 1})
            self.assertEqual(proof["route_proof_summary"]["coverage_rate"], 0.0)
            self.assertEqual(proof["route_proof_summary"]["covered_checkpoints"], 0)
            self.assertEqual(proof["route_proof_summary"]["total_checkpoints"], 2)
            self.assertEqual(proof["route_proof_summary"]["missing_checkpoints"], [0, 1])
            self.assertEqual(proof["route_proof_summary"]["gate_status"], "missing_live_frame")
            self.assertEqual(proof["debug_status"]["visual_gate_status"], "missing_live_frame")
            self.assertEqual(len(matcher.calls), 1)

    def test_invalid_route_returns_structured_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proof = build_visual_gate_proof(
                str(root / "missing.yaml"),
                str(root / "keyframes"),
                str(root / "live"),
                threshold=25,
                matcher=StubMatcher([]),
            )

            self.assertEqual(proof["route"]["status"], "invalid_route")
            self.assertEqual(proof["summary"]["status"], "invalid_route")
            self.assertEqual(proof["debug_status"]["visual_gate_status"], "invalid_route")
            self.assertEqual(proof["route_proof_summary"]["coverage_rate"], 0.0)
            self.assertEqual(proof["route_proof_summary"]["covered_checkpoints"], 0)
            self.assertEqual(proof["route_proof_summary"]["total_checkpoints"], 0)
            self.assertEqual(proof["route_proof_summary"]["missing_checkpoints"], [])
            self.assertEqual(proof["route_proof_summary"]["gate_status"], "invalid_route")
            self.assertIn("route file not found", proof["debug_status"]["failure_reason"])
            self.assertEqual(proof["checkpoints"], [])

    def test_cli_writes_json_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = root / "missing.yaml"
            output = root / "proof.json"

            with redirect_stdout(io.StringIO()):
                exit_code = main([
                    "--route-file",
                    str(route),
                    "--keyframe-dir",
                    str(root / "keyframes"),
                    "--live-frame-dir",
                    str(root / "live"),
                    "--threshold",
                    "25",
                    "--output",
                    str(output),
                ])

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["summary"]["status"], "invalid_route")
            self.assertEqual(payload["debug_status"]["visual_gate_status"], "invalid_route")

    def test_cli_returns_zero_when_all_checkpoints_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output = root / "proof.json"
            proof = {
                "route": {"path": "route.yaml", "contract_version": "fixed_route.v1", "total_checkpoints": 1},
                "checkpoints": [],
                "summary": {"status": "passed", "passed": 1, "failed": 0, "failure_reasons": {}},
                "debug_status": {"visual_gate_status": "passed"},
            }

            def fake_build(*_args, **kwargs):
                Path(kwargs["output_file"]).write_text(json.dumps(proof), encoding="utf-8")
                return proof

            with mock.patch("ros2_trashbot_nav.visual_gate_proof.build_visual_gate_proof", fake_build):
                with redirect_stdout(io.StringIO()):
                    exit_code = main([
                        "--route-file",
                        str(root / "fixed_route.yaml"),
                        "--keyframe-dir",
                        str(root / "keyframes"),
                        "--live-frame-dir",
                        str(root / "live"),
                        "--threshold",
                        "25",
                        "--output",
                        str(output),
                    ])

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["summary"]["status"], "passed")


if __name__ == "__main__":
    unittest.main()
