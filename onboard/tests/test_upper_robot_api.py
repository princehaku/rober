"""upper_robot_api 的底盘反馈 ACK 单元测试。

这些测试只覆盖非运动反馈链路，因为本轮任务禁止发送任何运动命令。
测试目标不是证明 HIL pass，而是防止 API status 再次退回硬编码 false。
`T=1001` 来自 WAVE ROVER vendor feedback，不能被包装成项目任务 ACK。
真实板上 yaw 可能不可用，所以 ACK 判定必须和 yaw 数值解析解耦。
fresh readback 的优先级高于 artifact，避免旧材料污染本轮证据。
artifact fallback 只接受 fresh 文件，stale 文件只能作为历史摘要。
status 允许发送 `T=130`，但必须持续关闭所有运动控制许可。
这些边界直接对应 sprint 的上车 evidence capture 缺口。
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "upper_robot_api.py"
# 脚本不在 Python package 中，测试必须按路径加载真实文件。
SPEC = importlib.util.spec_from_file_location("upper_robot_api", MODULE_PATH)
upper_robot_api = importlib.util.module_from_spec(SPEC)
# 这里显式断言 loader 存在，避免路径错误时测试静默跳过。
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(upper_robot_api)


class UpperRobotApiFeedbackAckTests(unittest.TestCase):
    """锁定 `/api/base/status.feedback_ack` 的新鲜证据和安全字段。"""

    def test_t1001_frame_allows_null_yaw(self) -> None:
        """ACK 只证明底盘反馈帧到达，不要求 yaw 可用于姿态发布。"""
        # 真实板上 yaw 可能是字符串 "null"，ACK 只证明 T=1001 到达。
        frame = {"T": 1001, "L": 0, "R": 0, "r": 0, "p": 0, "y": "null", "v": 10.5}

        # `y` 不参与 ACK，避免姿态不可用时把电压/轮速反馈一起丢掉。
        self.assertTrue(upper_robot_api.t1001_feedback_observed_in_frame(frame))
        # 部分 JSON 来源可能把 `T` 序列化成字符串，status 也要容错。
        self.assertEqual(1001, upper_robot_api.feedback_type_from_frame({"T": "1001", "y": None}))

    def test_feedback_ack_prefers_fresh_readback(self) -> None:
        """本次 readback 已观测 T=1001 时，stale artifact 不能改变来源。"""
        # status 必须优先使用本轮 readback，不能依赖旧 artifact 伪造新鲜 ACK。
        readback = {
            "feedback_ack": {
                "t1001_observed": True,
                "reason": "observed in test",
            }
        }
        stale_artifact = {
            "freshness": {"status": "stale"},
            "latest_t1001_observed_count": 3,
        }

        ack = upper_robot_api.feedback_ack_from_fresh_evidence(readback, stale_artifact)

        # stale artifact 仍可展示历史摘要，但不能覆盖 fresh_readback 来源。
        self.assertTrue(ack["t1001_observed"])
        self.assertEqual("fresh_readback", ack["source"])
        self.assertFalse(ack["robot_ack_connected"])

    def test_feedback_ack_accepts_only_fresh_artifact_fallback(self) -> None:
        """artifact 兜底必须受 freshness 限制，避免复用历史上车材料。"""
        # artifact 只有在 fresh 且包含 T=1001 计数时，才能作为 status ACK 兜底。
        readback = {"feedback_ack": {"t1001_observed": False, "reason": "not observed"}}
        fresh_artifact = {
            "freshness": {"status": "fresh"},
            "latest_t1001_observed_count": 1,
        }
        stale_artifact = {
            "freshness": {"status": "stale"},
            "latest_t1001_observed_count": 1,
        }

        fresh_ack = upper_robot_api.feedback_ack_from_fresh_evidence(readback, fresh_artifact)
        stale_ack = upper_robot_api.feedback_ack_from_fresh_evidence(readback, stale_artifact)

        # 只有 fresh artifact 能作为兜底，stale artifact 必须继续返回 false。
        self.assertTrue(fresh_ack["t1001_observed"])
        self.assertEqual("fresh_artifact", fresh_ack["source"])
        self.assertFalse(stale_ack["t1001_observed"])

    def test_base_status_reports_non_motion_readback_without_control_enable(self) -> None:
        """status 可以做只读反馈探测，但不能开启 safe_to_control。"""
        # /api/base/status 允许发送 T=130，但不得打开运动控制或交付成功标志。
        with tempfile.TemporaryDirectory() as temp_dir:
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                feedback_samples_artifact_path=str(Path(temp_dir) / "missing.json"),
            )
            fake_readback = {
                "feedback_ack": {"t1001_observed": True},
                "sends_commands": True,
                "sends_motion_commands": False,
            }

            # mock readback 可以验证 status 汇总，不需要在单元测试中打开串口。
            with mock.patch.object(upper_robot_api, "request_base_feedback_once", return_value=fake_readback):
                # 设备存在性和 pyserial 可用性也 mock，避免本地开发机依赖 `/dev/ttyS5`。
                with mock.patch.object(upper_robot_api, "describe_path", return_value={"exists": True}):
                    with mock.patch.object(upper_robot_api, "load_serial_module", return_value=(object(), None)):
                        status = api.base_status()

        # ACK 为 true 不能外溢成任何运动许可或任务完成结论。
        self.assertTrue(status["feedback_ack"]["t1001_observed"])
        self.assertEqual("fresh_readback", status["feedback_ack"]["source"])
        self.assertTrue(status["readback_sends_commands"])
        self.assertTrue(status["sends_commands"])
        # T=130 属于反馈请求；只要运动字段保持 false，就不会误导现场操作。
        self.assertFalse(status["sends_motion_commands"])
        self.assertFalse(status["safe_to_control"])
        self.assertFalse(status["primary_actions_enabled"])
        self.assertFalse(status["robot_control_executed"])


if __name__ == "__main__":
    unittest.main()
