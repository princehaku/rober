"""Nav2 参数合同的轻量静态测试。"""

from __future__ import annotations

import unittest
from pathlib import Path


PARAMS = Path(__file__).resolve().parents[1] / "src" / "ros2_trashbot_nav" / "config" / "nav2_params.yaml"


class Nav2ParamsContractTests(unittest.TestCase):
    """锁定实车短路线执行不再被雷达/局部 costmap 误障碍阻断。"""

    def test_regulated_pure_pursuit_disables_collision_detection_for_field_execution(self) -> None:
        """当前 O11/自主路线执行需要先证明底盘可动，不能在发 /cmd_vel 前被误障碍卡死。"""
        text = PARAMS.read_text(encoding="utf-8")
        follow_path_index = text.index("FollowPath:")
        next_section_index = text.index("\n\nplanner_server:", follow_path_index)
        follow_path_block = text[follow_path_index:next_section_index]

        self.assertIn("nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController", follow_path_block)
        self.assertIn("use_collision_detection: false", follow_path_block)
        self.assertIn("当前真机路线执行证明不能被雷达/局部 costmap 的误障碍卡死", follow_path_block)


if __name__ == "__main__":
    unittest.main()
