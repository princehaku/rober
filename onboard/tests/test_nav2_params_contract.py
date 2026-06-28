"""Nav2 参数合同的轻量静态测试。"""

from __future__ import annotations

import unittest
from pathlib import Path


PARAMS = Path(__file__).resolve().parents[1] / "src" / "ros2_trashbot_nav" / "config" / "nav2_params.yaml"


class Nav2ParamsContractTests(unittest.TestCase):
    """锁定实车短路线执行不再被雷达/局部 costmap 误障碍阻断。"""

    def test_map_server_declares_yaml_placeholder_for_bringup_rewrite(self) -> None:
        """Nav2 bringup 只有看到 yaml_filename 键，才会把 launch 的 map 参数重写给 map_server。"""
        text = PARAMS.read_text(encoding="utf-8")
        map_server_index = text.index("map_server:")
        next_section_index = text.index("\namcl:", map_server_index)
        map_server_block = text[map_server_index:next_section_index]

        self.assertIn("yaml_filename: \"\"", map_server_block)
        self.assertIn("topic_name: \"map\"", map_server_block)
        self.assertIn("frame_id: \"map\"", map_server_block)
        self.assertIn("map_server 会停在 unconfigured", map_server_block)

    def test_amcl_sets_default_initial_pose_to_publish_map_to_odom(self) -> None:
        """没有默认初始位姿时 AMCL 会 active 但不发布 map->odom，Nav2 costmap 会一直等 TF。"""
        text = PARAMS.read_text(encoding="utf-8")
        amcl_index = text.index("amcl:")
        next_section_index = text.index("\nbt_navigator:", amcl_index)
        amcl_block = text[amcl_index:next_section_index]

        self.assertIn("set_initial_pose: true", amcl_block)
        self.assertIn("initial_pose.x: 0.0", amcl_block)
        self.assertIn("initial_pose.y: 0.0", amcl_block)
        self.assertIn("initial_pose.yaw: 0.0", amcl_block)
        self.assertIn("PC 的 initialpose 刷新仍可覆盖这个默认值", amcl_block)

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
