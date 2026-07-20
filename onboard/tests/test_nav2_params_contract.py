"""Nav2 参数合同的轻量静态测试。"""

from __future__ import annotations

import unittest
from pathlib import Path


PARAMS = Path(__file__).resolve().parents[1] / "src" / "ros2_trashbot_nav" / "config" / "nav2_params.yaml"


class Nav2ParamsContractTests(unittest.TestCase):
    """锁定实车短路线同时具备 current scan 准入和执行期碰撞保护。"""

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

    def test_regulated_pure_pursuit_keeps_collision_detection_enabled(self) -> None:
        """同窗 obstacle-clear 只负责准入，controller 执行期仍必须持续做碰撞预测。"""
        text = PARAMS.read_text(encoding="utf-8")
        follow_path_index = text.index("FollowPath:")
        next_section_index = text.index("\n\nplanner_server:", follow_path_index)
        follow_path_block = text[follow_path_index:next_section_index]

        self.assertIn("nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController", follow_path_block)
        self.assertIn("use_collision_detection: true", follow_path_block)
        self.assertIn("同窗 scan 净空门只负责发车准入", follow_path_block)

    def test_obstacle_layer_requires_current_scan_without_history_persistence(self) -> None:
        """obstacle layer 不得用历史 scan 冒充 current clearance，并声明 10Hz 期望更新。"""
        text = PARAMS.read_text(encoding="utf-8")
        obstacle_index = text.index("    obstacle_layer:")
        next_section_index = text.index("    inflation_layer:", obstacle_index)
        obstacle_block = text[obstacle_index:next_section_index]

        self.assertIn("topic: /scan", obstacle_block)
        self.assertIn("observation_persistence: 0.0", obstacle_block)
        self.assertIn("expected_update_rate: 10.0", obstacle_block)
        self.assertIn("不把历史观测持久化成当前净空", obstacle_block)


if __name__ == "__main__":
    unittest.main()
