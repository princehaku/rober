#!/usr/bin/env python3
"""兼容 tech-plan 的 Upper API 测试入口。"""

# 实际合同测试长期位于 onboard/tests；这里仅复用同一测试类，避免复制或分叉用例。
from onboard.tests.test_upper_robot_api import UpperRobotApiFeedbackAckTests


# 显式导出可让 `python -m unittest <path>` 继续按既有验收命令收集测试。
__all__ = ["UpperRobotApiFeedbackAckTests"]
