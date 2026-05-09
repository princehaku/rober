import ast
from pathlib import Path
import unittest


BRINGUP_ROOT = Path(__file__).resolve().parents[1]
LAUNCH_ROOT = BRINGUP_ROOT / "launch"


def read_launch(name):
    return (LAUNCH_ROOT / name).read_text(encoding="utf-8")


def node_block(source, executable):
    start = source.index(f"executable='{executable}'")
    end = source.index("\n        ),", start)
    return source[start:end]


class LaunchContractStaticTest(unittest.TestCase):
    def test_bringup_delivery_parameters_go_to_task_orchestrator_not_map_recorder(self):
        source = read_launch("bringup.launch.py")

        task_block = source[source.index("executable='task_orchestrator'"):]
        map_block = source[source.index("executable='map_recorder'"):source.index("# --- Vision ---")]

        for key in (
            "'waypoint_file'",
            "'delivery_mode'",
            "'delivery_target'",
            "'return_target'",
            "'task_record_dir'",
            "'dropoff_timeout_sec'",
            "'navigation_timeout_sec'",
        ):
            self.assertIn(key, task_block)
            self.assertNotIn(key, map_block)

    def test_autonomous_declares_fixed_route_arguments_and_exclusive_conditions(self):
        source = read_launch("autonomous.launch.py")
        ast.parse(source)

        for argument in (
            "'navigation_mode'",
            "'route_file'",
            "'keyframe_dir'",
            "'enable_visual_gate'",
            "'visual_match_threshold'",
            "'fixed_route_dry_run'",
            "'debug_status_file'",
            "'route_debug_web'",
            "'operator_gateway'",
            "'operator_gateway_host'",
            "'operator_gateway_port'",
                    "'operator_gateway_collect_action'",
                    "'operator_gateway_dropoff_service'",
                    "'operator_status_file'",
                    "'operator_pose_topic'",
                    "'remote_bridge'",
            "'remote_cloud_base_url'",
            "'remote_robot_id'",
            "'remote_auth_token'",
            "'remote_poll_interval_sec'",
            "'remote_request_timeout_sec'",
        ):
            self.assertIn(argument, source)

        self.assertIn("executable='fixed_route_autonomy'", source)
        self.assertIn("executable='route_debug_web'", source)
        self.assertIn("fixed_route_condition", source)
        self.assertIn("waypoint_condition", source)
        self.assertIn("condition=waypoint_condition", source)
        self.assertIn("condition=fixed_route_condition", source)

    def test_autonomous_passes_debug_status_file_to_task_orchestrator(self):
        source = read_launch("autonomous.launch.py")
        ast.parse(source)

        task_block = source[
            source.index("executable='task_orchestrator'"):
            source.index("# Patrol scheduler")
        ]

        self.assertIn("'fixed_route_status_file': debug_status_file", task_block)

    def test_autonomous_can_start_operator_gateway(self):
        source = read_launch("autonomous.launch.py")
        gateway_block = source[source.index("executable='operator_gateway'"):]

        self.assertIn("condition=operator_gateway_condition", gateway_block)
        self.assertIn("'use_sim_time': use_sim_time", gateway_block)
        self.assertIn("'host': operator_gateway_host", gateway_block)
        self.assertIn("'port': operator_gateway_port", gateway_block)
        self.assertIn("'default_target': delivery_target", gateway_block)
        self.assertIn("'collect_action_name': operator_gateway_collect_action", gateway_block)
        self.assertIn("'dropoff_service_name': operator_gateway_dropoff_service", gateway_block)

    def test_launches_can_start_remote_bridge(self):
        for launch_name in ("bringup.launch.py", "autonomous.launch.py"):
            with self.subTest(launch_name=launch_name):
                source = read_launch(launch_name)
                ast.parse(source)
                remote_block = source[source.index("executable='remote_bridge'"):]

                for argument in (
                    "'remote_bridge'",
                    "'remote_cloud_base_url'",
                    "'remote_robot_id'",
                    "'remote_auth_token'",
                    "'remote_poll_interval_sec'",
                    "'remote_request_timeout_sec'",
                ):
                    self.assertIn(argument, source)
                remote_block = node_block(source, "remote_bridge")
                self.assertIn("condition=remote_bridge_condition", remote_block)
                self.assertIn("'cloud_base_url': remote_cloud_base_url", remote_block)
                self.assertIn("'robot_id': remote_robot_id", remote_block)
                self.assertIn("'request_timeout_sec': remote_request_timeout_sec", remote_block)
                self.assertIn("'collect_action_name': operator_gateway_collect_action", remote_block)
                self.assertIn("'dropoff_service_name': operator_gateway_dropoff_service", remote_block)

    def test_bringup_can_start_operator_gateway(self):
        source = read_launch("bringup.launch.py")
        ast.parse(source)
        gateway_block = source[source.index("executable='operator_gateway'"):]

        for argument in (
            "'operator_gateway'",
            "'operator_gateway_host'",
            "'operator_gateway_port'",
                "'operator_gateway_collect_action'",
                "'operator_gateway_dropoff_service'",
                "'operator_status_file'",
                "'operator_pose_topic'",
            ):
                self.assertIn(argument, source)
        self.assertIn("condition=IfCondition(operator_gateway)", gateway_block)
        self.assertIn("'default_target': delivery_target", gateway_block)
        self.assertIn("'collect_action_name': operator_gateway_collect_action", gateway_block)
        self.assertIn("'dropoff_service_name': operator_gateway_dropoff_service", gateway_block)
        self.assertIn("'status_file': operator_status_file", gateway_block)
        self.assertIn("'pose_topic': operator_pose_topic", gateway_block)

    def test_hardware_bridge_launches_with_canonical_serial_parameters(self):
        for launch_name in ("bringup.launch.py", "autonomous.launch.py"):
            with self.subTest(launch_name=launch_name):
                source = read_launch(launch_name)
                ast.parse(source)

                hardware_block = source[
                    source.index("executable='esp32_bridge'"):
                    source.index("# Nav2 bringup" if launch_name == "autonomous.launch.py" else "# --- Navigation ---")
                ]

                self.assertIn("'serial_port': serial_port", hardware_block)
                self.assertIn("'serial_baudrate': serial_baudrate", hardware_block)
                self.assertNotIn("'port': serial_port", hardware_block)
                self.assertNotIn("'baudrate': serial_baudrate", hardware_block)


if __name__ == "__main__":
    unittest.main()
