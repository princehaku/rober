from pathlib import Path
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MSG = PACKAGE_ROOT / "msg" / "TrashStatus.msg"
CONTRACT = PACKAGE_ROOT.parents[1] / "docs" / "vision" / "trash_status_contract.md"


class TrashStatusContractStaticTest(unittest.TestCase):
    def test_message_fields_stay_in_stable_order(self):
        source = MSG.read_text(encoding="utf-8")
        fields = [
            line.split("#", 1)[0].strip()
            for line in source.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

        self.assertEqual(
            fields,
            [
                "string frame_id",
                "float64 x",
                "float64 y",
                "float64 z",
                "int8 confidence",
                "int8 trash_type",
                "bool is_bin",
                "float64 timestamp",
            ],
        )

    def test_contract_documents_behavior_facing_semantics(self):
        contract = CONTRACT.read_text(encoding="utf-8")

        for phrase in (
            "stable behavior-facing perception contract",
            "not `map` frame object poses",
            "`0=unknown`, `1=organic`, `2=recyclable`, `3=general`",
            "delivery navigation and dropoff confirmation",
            "OpenCV, YOLO, RT-DETR",
        ):
            self.assertIn(phrase, contract)


if __name__ == "__main__":
    unittest.main()
