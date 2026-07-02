import ast
from pathlib import Path
import unittest


BRINGUP_ROOT = Path(__file__).resolve().parents[1]
LAUNCH_ROOT = BRINGUP_ROOT / "launch"
RVIZ_ROOT = BRINGUP_ROOT / "rviz"


def read_launch(name):
    return (LAUNCH_ROOT / name).read_text(encoding="utf-8")


def read_rviz(name):
    return (RVIZ_ROOT / name).read_text(encoding="utf-8")


def node_block(source, executable):
    start = source.index(f"executable='{executable}'")
    end = source.index("\n        ),", start)
    return source[start:end]


class LaunchContractStaticTest(unittest.TestCase):
    def test_bringup_delivery_parameters_go_to_task_orchestrator_not_map_recorder(self):
        source = read_launch("bringup.launch.py")

        task_block = source[source.index("executable='task_orchestrator'"):]
        map_block = source[
            source.index("executable='map_recorder'"):
            source.index("executable='task_orchestrator'")
        ]

        for key in (
            "'waypoint_file'",
            "'delivery_mode'",
            "'delivery_target'",
            "'return_target'",
            "'elevator_assist_enabled'",
            "'elevator_assist_mode'",
            "'elevator_assist_target_floor'",
            "'elevator_assist_dry_run_failure'",
            "'task_record_dir'",
            "'dropoff_timeout_sec'",
            "'navigation_timeout_sec'",
        ):
            if key == "'elevator_assist_target_floor'":
                self.assertIn("'elevator_assist_target_floor': ParameterValue(", task_block)
            else:
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
            "'nav2_stack_only'",
            "'debug_status_file'",
            "'route_debug_web'",
            "'operator_gateway'",
            "'operator_gateway_host'",
            "'operator_gateway_port'",
            "'operator_gateway_collect_action'",
            "'operator_gateway_dropoff_service'",
            "'operator_status_file'",
            "'operator_pose_topic'",
            "'operator_hardware_proof_ref'",
            "'remote_bridge'",
            "'remote_cloud_base_url'",
            "'remote_robot_id'",
            "'remote_auth_token'",
            "'remote_poll_interval_sec'",
            "'remote_request_timeout_sec'",
            "'elevator_assist_enabled'",
            "'elevator_assist_mode'",
            "'elevator_assist_target_floor'",
            "'elevator_assist_dry_run_failure'",
        ):
            self.assertIn(argument, source)

        self.assertIn("executable='fixed_route_autonomy'", source)
        self.assertIn("executable='route_debug_web'", source)
        self.assertIn("fixed_route_condition", source)
        self.assertIn("waypoint_condition", source)
        self.assertIn("condition=waypoint_condition", source)
        self.assertIn("condition=fixed_route_condition", source)
        self.assertIn("'enable_visual_gate', default_value='false'", source)
        self.assertIn("'fixed_route_dry_run', default_value='false'", source)

    def test_autonomous_nav2_stack_only_skips_business_navigation_nodes(self):
        # 受管 Nav2 lifecycle start 只启动底盘 bridge/传感器/Nav2，不启动业务导航节点。
        # 巡逻、任务编排和固定路线节点必须显式受 nav2_stack_only gate 保护。
        source = read_launch("autonomous.launch.py")
        ast.parse(source)

        self.assertIn("'nav2_stack_only', default_value='false'", source)
        self.assertIn("full_stack_condition", source)
        for executable in (
            "task_orchestrator",
            "nav_to_goal",
            "waypoint_manager",
            "fixed_route_autonomy",
            "operator_gateway",
            "remote_bridge",
        ):
            block = node_block(source, executable)
            self.assertIn("condition=", block)
        self.assertIn("full_stack_expression", source)
        self.assertIn("nav2_stack_only", source)

    def test_autonomous_nav2_stack_only_can_start_lidar_scan_input_without_business_nodes(self):
        # Nav2/AMCL 需要 /scan 和 base_link->laser_frame；stack-only 不能只拉 Nav2 bringup。
        source = read_launch("autonomous.launch.py")
        ast.parse(source)

        lidar_block = node_block(source, "lidar_driver")
        base_block = node_block(source, "esp32_bridge")

        for argument in (
            "'base_enabled'",
            "'lidar_enabled'",
            "'lidar_serial_port'",
            "'lidar_serial_baudrate'",
            "'lidar_frame_id'",
            "'lidar_scan_topic'",
            "'lidar_raw_packet_topic'",
            "'lidar_publish_raw_packets'",
            "'lidar_mock_packets'",
            "'lidar_mock_scan'",
            "'static_laser_tf_enabled'",
            "'base_frame_id'",
            "'laser_tf_x'",
            "'laser_tf_y'",
            "'laser_tf_z'",
            "'laser_tf_roll'",
            "'laser_tf_pitch'",
            "'laser_tf_yaw'",
        ):
            self.assertIn(argument, source)

        self.assertIn("'base_enabled', default_value='true'", source)
        self.assertIn("'lidar_enabled', default_value='false'", source)
        self.assertIn("condition=IfCondition(base_enabled)", base_block)
        self.assertIn("condition=IfCondition(lidar_enabled)", lidar_block)
        self.assertIn("'serial_port': lidar_serial_port", lidar_block)
        self.assertIn("'scan_topic': lidar_scan_topic", lidar_block)
        self.assertIn("name='static_laser_tf'", source)
        self.assertIn("condition=IfCondition(static_laser_tf_enabled)", source)

    def test_autonomous_passes_debug_status_file_to_task_orchestrator(self):
        source = read_launch("autonomous.launch.py")
        ast.parse(source)

        task_block = source[
            source.index("executable='task_orchestrator'"):
            source.index("# Patrol scheduler")
        ]

        self.assertIn("'fixed_route_status_file': debug_status_file", task_block)

    def test_bringup_default_elevator_assist_off_and_pass_to_task_orchestrator(self):
        # bringup 默认只做基础链路，优先保证“上电可控”和“快速退化”，因此不默认触发电梯子状态机。
        launch_name = "bringup.launch.py"
        source = read_launch(launch_name)
        ast.parse(source)
        task_block = source[
            source.index("executable='task_orchestrator'"):
            source.index(
                "Node(\n            package='ros2_trashbot_behavior',\n            executable='operator_gateway'"
            )
        ]

        self.assertIn("'elevator_assist_enabled', default_value='false'", source)
        self.assertIn("'elevator_assist_mode', default_value='dry_run'", source)
        self.assertIn("'elevator_assist_target_floor', default_value='1'", source)
        self.assertIn("'elevator_assist_dry_run_failure', default_value=''", source)
        self.assertIn("'elevator_assist_enabled': elevator_assist_enabled", task_block)
        self.assertIn("'elevator_assist_mode': elevator_assist_mode", task_block)
        self.assertIn("'elevator_assist_target_floor': ParameterValue(", task_block)
        self.assertIn(
            "'elevator_assist_dry_run_failure': elevator_assist_dry_run_failure",
            task_block,
        )

    def test_autonomous_default_elevator_assist_on_and_pass_to_task_orchestrator(self):
        # autonomous 是主链路演进入口，默认开启电梯 dry-run，便于主线证据链可复现，不代表真实电梯能力已完成交付。
        launch_name = "autonomous.launch.py"
        source = read_launch(launch_name)
        ast.parse(source)
        task_block = source[
            source.index("executable='task_orchestrator'"):
            source.index("# Patrol scheduler")
        ]

        self.assertIn("'elevator_assist_enabled', default_value='true'", source)
        self.assertIn("'elevator_assist_mode', default_value='dry_run'", source)
        self.assertIn("'elevator_assist_target_floor', default_value='1'", source)
        self.assertIn("'elevator_assist_dry_run_failure', default_value=''", source)
        self.assertIn("'elevator_assist_enabled': elevator_assist_enabled", task_block)
        self.assertIn("'elevator_assist_mode': elevator_assist_mode", task_block)
        self.assertIn("'elevator_assist_target_floor': elevator_assist_target_floor", task_block)
        self.assertIn(
            "'elevator_assist_dry_run_failure': elevator_assist_dry_run_failure",
            task_block,
        )

    def test_launches_do_not_start_retired_trash_detector(self):
        for launch_name in ("learn.launch.py", "bringup.launch.py", "autonomous.launch.py"):
            with self.subTest(launch_name=launch_name):
                source = read_launch(launch_name)
                ast.parse(source)

                self.assertNotIn("trash_detector", source)
                self.assertNotIn("vision_detection_confidence", source)
                self.assertNotIn("save_detection_samples", source)

    def test_rviz_companion_observes_nav2_without_goal_tool(self):
        # RViz2 是工程观察面，不是普通用户发车入口；这里锁住只读地图/雷达/相机/Nav2 诊断层。
        launch_source = read_launch("rviz.launch.py")
        rviz_source = read_rviz("trashbot_nav.rviz")
        ast.parse(launch_source)

        self.assertIn("trashbot_nav.rviz", launch_source)
        self.assertIn('executable="rviz2"', launch_source)
        for expected in (
            "Fixed Frame: map",
            "Name: Map",
            "Value: /map",
            "Name: LaserScan",
            "Value: /scan",
            "Name: TF",
            "Name: Nav2 Path",
            "Value: /plan",
            "Name: Nav2 Local Plan",
            "Value: /local_plan",
            "Name: AMCL Pose",
            "Value: /amcl_pose",
            "Name: Camera Image",
            "Value: /camera/image_raw",
            "Name: Nav2 Global Costmap",
            "Value: /global_costmap/costmap",
            "Value: /global_costmap/costmap_updates",
            "Name: Nav2 Local Costmap",
            "Value: /local_costmap/costmap",
            "Value: /local_costmap/costmap_updates",
        ):
            self.assertIn(expected, rviz_source)

        self.assertNotIn("nav2_rviz_plugins/GoalTool", rviz_source)
        self.assertNotIn("SetInitialPose", rviz_source)

    def test_rviz_launch_is_read_only_observation_view(self):
        # RViz 入口只帮助现场看 /map、/scan、相机、TF、路线和定位；目标下发仍必须走 PC 安全确认链路。
        launch_source = read_launch("rviz.launch.py")
        ast.parse(launch_source)
        rviz_source = (RVIZ_ROOT / "trashbot_nav.rviz").read_text(encoding="utf-8")
        cmake_source = (BRINGUP_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")

        self.assertIn("package=\"rviz2\"", launch_source)
        self.assertIn("trashbot_nav.rviz", launch_source)
        self.assertIn("install(DIRECTORY launch rviz", cmake_source)
        for token in ("Fixed Frame: map", "Value: /map", "Value: /scan", "Value: /camera/image_raw", "Value: /plan", "Value: /amcl_pose"):
            self.assertIn(token, rviz_source)
        self.assertNotIn("SetInitialPose", rviz_source)
        self.assertNotIn("SetGoal", rviz_source)
        self.assertNotIn("Nav Goal", rviz_source)

    def test_foxglove_bridge_launch_is_remote_observation_only(self):
        # Foxglove 给远程浏览器看图和雷达，不能绕过 PC 安全确认变成另一条控制入口。
        source = read_launch("foxglove_bridge.launch.py")
        ast.parse(source)

        for expected in (
            'default_value="0.0.0.0"',
            'default_value="8765"',
            'package="foxglove_bridge"',
            'executable="foxglove_bridge"',
            '"topic_whitelist": observe_topic_whitelist',
            '"client_topic_whitelist": ["(?!)"]',
            '"service_whitelist": ["(?!)"]',
            '"param_whitelist": ["(?!)"]',
            '"capabilities": ["connectionGraph", "assets", "time"]',
            "^/(map|map_metadata|scan|tf|tf_static|odom|plan|local_plan|amcl_pose|pose)$",
            "^/(global_costmap|local_costmap)/(costmap|costmap_updates)$",
            "^/camera/(image_raw|camera_info)$",
            "^/foxglove_bridge/sysinfo$",
        ):
            self.assertIn(expected, source)

        for forbidden in (
            "/cmd_vel",
            "clientPublish",
            '"services"',
            '"parameters"',
            '"parametersSubscribe"',
            "/api/robot-control",
            "/trashbot/collect_trash",
            "/trashbot/confirm_dropoff",
        ):
            self.assertNotIn(forbidden, source)

    def test_field_camera_default_uses_verified_capture_device(self):
        # 实板上 /dev/video0 是 Cedrus decoder；默认指向 /dev/video1，避免相机启用后误绑非采集节点。
        for launch_name in ("bringup.launch.py", "learn.launch.py"):
            with self.subTest(launch_name=launch_name):
                source = read_launch(launch_name)
                ast.parse(source)
                camera_block = node_block(source, "camera_publisher")

                self.assertIn("'camera_enabled', default_value='false'", source)
                self.assertIn("'camera_device', default_value='/dev/video1'", source)
                self.assertNotIn("'camera_device', default_value='/dev/video0'", source)
                self.assertIn("condition=IfCondition(camera_enabled)", camera_block)
                self.assertIn("'device': camera_device", camera_block)

    def test_learn_launch_can_start_fixed_route_recorder(self):
        source = read_launch("learn.launch.py")
        ast.parse(source)

        for argument in (
            "'route_recorder'",
            "'route_output_dir'",
            "'route_camera_topic'",
            "'route_odom_topic'",
            "'route_min_distance_m'",
            "'route_frame_id'",
            "'route_id'",
            "'route_sample_manifest_name'",
            "'route_sample_manifest_max_entries'",
        ):
            self.assertIn(argument, source)

        recorder_block = node_block(source, "route_data_recorder")
        self.assertIn("condition=IfCondition(route_recorder)", recorder_block)
        self.assertIn("'output_dir': route_output_dir", recorder_block)
        self.assertIn("'camera_topic': route_camera_topic", recorder_block)
        self.assertIn("'odom_topic': route_odom_topic", recorder_block)
        self.assertIn("'min_distance_m': route_min_distance_m", recorder_block)
        self.assertIn("'route_frame_id': route_frame_id", recorder_block)
        self.assertIn("'route_id': route_id", recorder_block)
        self.assertIn("'sample_manifest_name': route_sample_manifest_name", recorder_block)
        self.assertIn("'sample_manifest_max_entries': route_sample_manifest_max_entries", recorder_block)

    def test_learn_launch_can_start_no_motion_sensor_capture_stack(self):
        # no-motion 现场采集必须一条 learn.launch 拉起 SLAM、传感器、route recorder 和 synthetic odom。
        source = read_launch("learn.launch.py")
        ast.parse(source)

        for argument in (
            "'camera_enabled'",
            "'camera_device'",
            "'camera_topic'",
            "'camera_frame_id'",
            "'camera_width'",
            "'camera_height'",
            "'camera_fps'",
            "'waypoint_manager'",
            "'lidar_enabled'",
            "'lidar_serial_port'",
            "'lidar_serial_baudrate'",
            "'lidar_frame_id'",
            "'lidar_scan_topic'",
            "'lidar_raw_packet_topic'",
            "'lidar_publish_raw_packets'",
            "'lidar_range_min'",
            "'lidar_range_max'",
            "'lidar_scan_time'",
            "'lidar_time_increment'",
            "'lidar_mock_packets'",
            "'lidar_mock_scan'",
            "'static_laser_tf_enabled'",
            "'base_frame_id'",
            "'no_motion_static_odom_tf'",
            "'no_motion_mock_odom_enabled'",
            "'no_motion_mock_odom_topic'",
            "'no_motion_mock_odom_rate'",
            "'no_motion_odom_frame_id'",
            "'slam_map_frame'",
            "'slam_odom_frame'",
            "'slam_base_frame'",
            "'map_dir'",
            "'default_map_name'",
        ):
            self.assertIn(argument, source)

        camera_block = node_block(source, "camera_publisher")
        lidar_block = node_block(source, "lidar_driver")

        for default_off in (
            "'camera_enabled', default_value='false'",
            "'lidar_enabled', default_value='false'",
            "'static_laser_tf_enabled', default_value='false'",
            "'no_motion_static_odom_tf', default_value='false'",
            "'no_motion_mock_odom_enabled', default_value='false'",
        ):
            self.assertIn(default_off, source)

        self.assertIn("condition=IfCondition(camera_enabled)", camera_block)
        self.assertIn("'device': camera_device", camera_block)
        self.assertIn("'topic': camera_topic", camera_block)
        self.assertIn("condition=IfCondition(lidar_enabled)", lidar_block)
        self.assertIn("'serial_port': lidar_serial_port", lidar_block)
        self.assertIn("'scan_topic': lidar_scan_topic", lidar_block)
        self.assertIn("'range_min': lidar_range_min", lidar_block)
        self.assertIn("'range_max': lidar_range_max", lidar_block)
        self.assertIn("'scan_time': lidar_scan_time", lidar_block)
        self.assertIn("'time_increment': lidar_time_increment", lidar_block)

        self.assertIn("name='static_laser_tf'", source)
        self.assertIn("condition=IfCondition(static_laser_tf_enabled)", source)
        self.assertIn("name='no_motion_static_odom_tf'", source)
        self.assertIn("condition=IfCondition(no_motion_static_odom_tf)", source)
        self.assertIn("message.header.frame_id=odom_frame", source)
        self.assertIn("message.child_frame_id=base_frame", source)
        self.assertIn("'python3'", source)
        self.assertIn('node=Node("no_motion_mock_odom_pub")', source)
        self.assertIn("ExecuteProcess(", source)
        self.assertIn("condition=IfCondition(no_motion_mock_odom_enabled)", source)
        self.assertNotIn("'/cmd_vel'", source)
        self.assertIn("'map_frame': slam_map_frame", source)
        self.assertIn("'odom_frame': slam_odom_frame", source)
        self.assertIn("'base_frame': slam_base_frame", source)
        self.assertIn("'map_dir': map_dir", source)
        self.assertIn("'default_map_name': default_map_name", source)

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
        self.assertIn("'hardware_proof_ref': operator_hardware_proof_ref", gateway_block)

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
            "'operator_hardware_proof_ref'",
            ):
                self.assertIn(argument, source)
        self.assertIn("condition=IfCondition(operator_gateway)", gateway_block)
        self.assertIn("'default_target': delivery_target", gateway_block)
        self.assertIn("'collect_action_name': operator_gateway_collect_action", gateway_block)
        self.assertIn("'dropoff_service_name': operator_gateway_dropoff_service", gateway_block)
        self.assertIn("'status_file': operator_status_file", gateway_block)
        self.assertIn("'pose_topic': operator_pose_topic", gateway_block)
        self.assertIn("'hardware_proof_ref': operator_hardware_proof_ref", gateway_block)

    def test_bringup_can_disable_base_for_sensor_only_smoke(self):
        # sensor-only smoke 需要避开 /dev/ttyS5 竞争，因此 esp32 bridge 必须单独门控。
        source = read_launch("bringup.launch.py")
        ast.parse(source)
        base_block = node_block(source, "esp32_bridge")

        self.assertIn("'base_enabled', default_value='true'", source)
        self.assertIn("condition=IfCondition(base_enabled)", base_block)

    def test_bringup_can_start_lidar_driver_with_explicit_parameters(self):
        # LiDAR 默认关闭，避免开发机无串口时把 smoke 失败误读成主链路回归。
        source = read_launch("bringup.launch.py")
        ast.parse(source)
        lidar_block = node_block(source, "lidar_driver")

        for argument in (
            "'lidar_enabled'",
            "'lidar_serial_port'",
            "'lidar_serial_baudrate'",
            "'lidar_frame_id'",
            "'lidar_scan_topic'",
            "'lidar_raw_packet_topic'",
            "'lidar_publish_raw_packets'",
            "'lidar_mock_packets'",
            "'lidar_mock_scan'",
        ):
            self.assertIn(argument, source)

        self.assertIn("condition=IfCondition(lidar_enabled)", lidar_block)
        self.assertIn("'serial_port': lidar_serial_port", lidar_block)
        self.assertIn("'serial_baudrate': lidar_serial_baudrate", lidar_block)
        self.assertIn("'frame_id': lidar_frame_id", lidar_block)
        self.assertIn("'scan_topic': lidar_scan_topic", lidar_block)
        self.assertIn("'publish_raw_packets': lidar_publish_raw_packets", lidar_block)
        self.assertIn("'mock_packets': lidar_mock_packets", lidar_block)
        self.assertIn("'mock_scan': lidar_mock_scan", lidar_block)

    def test_learn_and_bringup_start_free_roam_runtime_with_explicit_motion_unlock_args(self):
        # PC 自动扫图 start/stop 需要真实节点接参数；launch 默认仍必须锁住 /cmd_vel 发布。
        for launch_name in ("learn.launch.py", "bringup.launch.py"):
            with self.subTest(launch_name=launch_name):
                source = read_launch(launch_name)
                ast.parse(source)
                free_roam_block = node_block(source, "free_roam_autonomy_node")

                self.assertIn("'free_roam_autonomy_enabled'", source)
                self.assertIn("default_value='true'", source)
                self.assertIn("'free_roam_autonomy_artifact_path'", source)
                self.assertIn("'free_roam_autonomy_enable_cmd_vel_publish'", source)
                self.assertIn("'free_roam_autonomy_motion_hil_unlocked'", source)
                self.assertIn("condition=IfCondition(free_roam_autonomy_enabled)", free_roam_block)
                self.assertIn("name='free_roam_autonomy'", free_roam_block)
                self.assertIn("'scan_topic': lidar_scan_topic", free_roam_block)
                self.assertIn("'map_topic': '/map'", free_roam_block)
                self.assertIn("'artifact_path': free_roam_autonomy_artifact_path", free_roam_block)
                self.assertIn("'enable_cmd_vel_publish': free_roam_autonomy_enable_cmd_vel_publish", free_roam_block)
                self.assertIn("'motion_hil_unlocked': free_roam_autonomy_motion_hil_unlocked", free_roam_block)
                self.assertIn("default_value='false'", source)

    def test_bringup_can_publish_smoke_only_static_laser_tf(self):
        # 该静态 TF 只用于拓扑 smoke，不代表 base_link 到 laser_frame 已完成机械标定。
        source = read_launch("bringup.launch.py")
        ast.parse(source)
        tf_block = node_block(source, "static_transform_publisher")

        for argument in (
            "'static_laser_tf_enabled'",
            "'base_frame_id'",
            "'laser_tf_x'",
            "'laser_tf_y'",
            "'laser_tf_z'",
            "'laser_tf_roll'",
            "'laser_tf_pitch'",
            "'laser_tf_yaw'",
        ):
            self.assertIn(argument, source)

        self.assertIn("condition=IfCondition(static_laser_tf_enabled)", tf_block)
        self.assertIn("base_frame_id", tf_block)
        self.assertIn("lidar_frame_id", tf_block)

    def test_hardware_bridge_launches_with_canonical_serial_parameters(self):
        for launch_name in ("bringup.launch.py", "autonomous.launch.py"):
            with self.subTest(launch_name=launch_name):
                source = read_launch(launch_name)
                ast.parse(source)

                hardware_block = source[
                    source.index("executable='esp32_bridge'"):
                    source.index("executable='waypoint_manager'" if launch_name == "bringup.launch.py" else "# Nav2 bringup")
                ]

                self.assertIn("'serial_port': serial_port", hardware_block)
                self.assertIn("'serial_baudrate': serial_baudrate", hardware_block)
                self.assertNotIn("'port': serial_port", hardware_block)
                self.assertNotIn("'baudrate': serial_baudrate", hardware_block)

    def test_hardware_bridge_launches_with_vendor_pwm_default_and_diagnostic_overrides(self):
        # bringup/autonomous 默认必须和硬件 bridge 纯参数默认一致，避免 Nav2 与手动入口漂到不同控制面。
        for launch_name in ("bringup.launch.py", "autonomous.launch.py"):
            with self.subTest(launch_name=launch_name):
                source = read_launch(launch_name)
                ast.parse(source)
                hardware_block = source[
                    source.index("executable='esp32_bridge'"):
                    source.index("executable='waypoint_manager'" if launch_name == "bringup.launch.py" else "# Nav2 bringup")
                ]

                self.assertIn("'command_mode', default_value='pwm'", source)
                self.assertIn("maps to vendor T=11 PWM", source)
                self.assertIn("ros/T=13 and speed/T=1 remain explicit diagnostics", source)
                self.assertIn("'pwm_min_abs', default_value='164'", source)
                self.assertIn("'pwm_max_abs', default_value='164'", source)
                self.assertIn("'command_mode': command_mode", hardware_block)
                self.assertIn("'pwm_min_abs': pwm_min_abs", hardware_block)
                self.assertIn("'pwm_max_abs': pwm_max_abs", hardware_block)


if __name__ == "__main__":
    unittest.main()
