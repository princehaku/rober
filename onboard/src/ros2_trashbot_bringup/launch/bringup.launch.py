"""Main bringup launch - starts all trashbot nodes together."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition


def generate_launch_description():
    # Arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock')

    serial_port_arg = DeclareLaunchArgument(
        'serial_port', default_value='/dev/ttyUSB0',
        description='UART device for the WAVE ROVER ESP32 controller')

    serial_baudrate_arg = DeclareLaunchArgument(
        'serial_baudrate', default_value='115200',
        description='UART baud rate for the WAVE ROVER ESP32 controller')

    command_mode_arg = DeclareLaunchArgument(
        'command_mode', default_value='speed',
        description='WAVE ROVER command mode: speed uses T=1, ros uses T=13')

    track_width_arg = DeclareLaunchArgument(
        'track_width_m', default_value='0.172',
        description='WAVE ROVER differential drive track width in meters')

    max_wheel_speed_arg = DeclareLaunchArgument(
        'max_wheel_speed_mps', default_value='1.3',
        description='Wheel speed used to normalize T=1 speed commands')

    waypoint_file_arg = DeclareLaunchArgument(
        'waypoint_file', default_value='~/.ros/trashbot_maps/waypoints.yaml',
        description='Path to saved waypoint YAML')

    delivery_mode_arg = DeclareLaunchArgument(
        'delivery_mode', default_value='dry_run',
        description='Delivery mode: dry_run or waypoint')

    delivery_target_arg = DeclareLaunchArgument(
        'delivery_target', default_value='trash_station',
        description='Waypoint name for trash station delivery')

    return_target_arg = DeclareLaunchArgument(
        'return_target', default_value='',
        description='Optional waypoint name to return to after dropoff')

    elevator_assist_enabled_arg = DeclareLaunchArgument(
        'elevator_assist_enabled', default_value='false',
        description='Enable elevator assisted delivery dry-run subflow')

    elevator_assist_mode_arg = DeclareLaunchArgument(
        'elevator_assist_mode', default_value='dry_run',
        description='Elevator assisted delivery mode; dry_run is the only software-only mode')

    elevator_assist_target_floor_arg = DeclareLaunchArgument(
        'elevator_assist_target_floor', default_value='1',
        description='Target floor used in elevator assisted delivery dry-run records')

    elevator_assist_dry_run_failure_arg = DeclareLaunchArgument(
        'elevator_assist_dry_run_failure', default_value='',
        description='Optional dry-run failure: door_timeout, target_floor_unconfirmed, unsafe_to_exit')

    task_record_dir_arg = DeclareLaunchArgument(
        'task_record_dir', default_value='~/.ros/trashbot_tasks',
        description='Directory for delivery task records')

    dropoff_timeout_sec_arg = DeclareLaunchArgument(
        'dropoff_timeout_sec', default_value='30.0',
        description='Delivery dropoff timeout in seconds')

    navigation_timeout_sec_arg = DeclareLaunchArgument(
        'navigation_timeout_sec', default_value='120.0',
        description='Delivery navigation timeout in seconds')

    operator_gateway_arg = DeclareLaunchArgument(
        'operator_gateway', default_value='false',
        description='Start local HTTP operator gateway')

    operator_gateway_host_arg = DeclareLaunchArgument(
        'operator_gateway_host', default_value='0.0.0.0',
        description='Operator gateway bind host')

    operator_gateway_port_arg = DeclareLaunchArgument(
        'operator_gateway_port', default_value='8766',
        description='Operator gateway HTTP port')

    operator_gateway_collect_action_arg = DeclareLaunchArgument(
        'operator_gateway_collect_action', default_value='/trashbot/collect_trash',
        description='Operator gateway collect action name')

    operator_gateway_dropoff_service_arg = DeclareLaunchArgument(
        'operator_gateway_dropoff_service', default_value='/trashbot/confirm_dropoff',
        description='Operator gateway dropoff confirmation service name')

    operator_status_file_arg = DeclareLaunchArgument(
        'operator_status_file', default_value='/tmp/trashbot_operator_status.json',
        description='Operator gateway status JSON path')

    operator_pose_topic_arg = DeclareLaunchArgument(
        'operator_pose_topic', default_value='/amcl_pose',
        description='Pose topic used by the operator gateway live location view')

    operator_hardware_proof_ref_arg = DeclareLaunchArgument(
        'operator_hardware_proof_ref', default_value='',
        description='Optional software-proof artifact path for diagnostics.hardware_proof (not HIL evidence)')

    remote_bridge_arg = DeclareLaunchArgument(
        'remote_bridge', default_value='false',
        description='Start outbound 4G remote bridge')

    remote_cloud_base_url_arg = DeclareLaunchArgument(
        'remote_cloud_base_url', default_value='',
        description='Remote cloud base URL for outbound polling')

    remote_robot_id_arg = DeclareLaunchArgument(
        'remote_robot_id', default_value='trashbot-001',
        description='Remote cloud robot identifier')

    remote_auth_token_arg = DeclareLaunchArgument(
        'remote_auth_token', default_value='',
        description='Remote cloud bearer token')

    remote_poll_interval_sec_arg = DeclareLaunchArgument(
        'remote_poll_interval_sec', default_value='2.0',
        description='Remote bridge polling interval in seconds')

    remote_request_timeout_sec_arg = DeclareLaunchArgument(
        'remote_request_timeout_sec', default_value='5.0',
        description='Remote bridge HTTP request timeout in seconds')

    lidar_enabled_arg = DeclareLaunchArgument(
        'lidar_enabled', default_value='false',
        description='Start ROS2 LiDAR driver; default false avoids blocking bringup without serial hardware')

    lidar_serial_port_arg = DeclareLaunchArgument(
        'lidar_serial_port', default_value='/dev/ttyUSB0',
        description='LiDAR serial device placeholder from local vendor reference; confirm on robot')

    lidar_serial_baudrate_arg = DeclareLaunchArgument(
        'lidar_serial_baudrate', default_value='150000',
        description='LiDAR baud rate from docs/vendor/lidar_ros reference')

    lidar_frame_id_arg = DeclareLaunchArgument(
        'lidar_frame_id', default_value='laser_frame',
        description='LiDAR frame id; must match measured base_link static TF on hardware')

    lidar_scan_topic_arg = DeclareLaunchArgument(
        'lidar_scan_topic', default_value='/scan',
        description='LaserScan topic consumed by Nav2/SLAM')

    lidar_raw_packet_topic_arg = DeclareLaunchArgument(
        'lidar_raw_packet_topic', default_value='/lidar/raw_packet',
        description='Optional raw LiDAR packet topic')

    lidar_publish_raw_packets_arg = DeclareLaunchArgument(
        'lidar_publish_raw_packets', default_value='false',
        description='Publish raw 0xAA55 packets for diagnostics')

    lidar_range_min_arg = DeclareLaunchArgument(
        'lidar_range_min', default_value='0.05',
        description='LiDAR LaserScan range_min in meters; tune after real point cloud validation')

    lidar_range_max_arg = DeclareLaunchArgument(
        'lidar_range_max', default_value='8.0',
        description='LiDAR LaserScan range_max in meters; tune after real point cloud validation')

    lidar_scan_time_arg = DeclareLaunchArgument(
        'lidar_scan_time', default_value='0.1',
        description='LiDAR LaserScan scan_time placeholder in seconds; measure on real hardware')

    lidar_time_increment_arg = DeclareLaunchArgument(
        'lidar_time_increment', default_value='0.0001',
        description='LiDAR LaserScan time_increment placeholder in seconds; measure on real hardware')

    lidar_tf_x_arg = DeclareLaunchArgument(
        'lidar_tf_x', default_value='0.0',
        description='Placeholder LiDAR x offset from base_link in meters; measure on real robot')

    lidar_tf_y_arg = DeclareLaunchArgument(
        'lidar_tf_y', default_value='0.0',
        description='Placeholder LiDAR y offset from base_link in meters; measure on real robot')

    lidar_tf_z_arg = DeclareLaunchArgument(
        'lidar_tf_z', default_value='0.0',
        description='Placeholder LiDAR z offset from base_link in meters; measure on real robot')

    lidar_tf_roll_arg = DeclareLaunchArgument(
        'lidar_tf_roll', default_value='0.0',
        description='Placeholder LiDAR roll from base_link in radians; measure on real robot')

    lidar_tf_pitch_arg = DeclareLaunchArgument(
        'lidar_tf_pitch', default_value='0.0',
        description='Placeholder LiDAR pitch from base_link in radians; measure on real robot')

    lidar_tf_yaw_arg = DeclareLaunchArgument(
        'lidar_tf_yaw', default_value='0.0',
        description='Placeholder LiDAR yaw from base_link in radians; measure on real robot')

    lidar_mock_packets_arg = DeclareLaunchArgument(
        'lidar_mock_packets', default_value='',
        description='Pipe-separated hex packets for software-only LiDAR verification')

    lidar_mock_scan_arg = DeclareLaunchArgument(
        'lidar_mock_scan', default_value='false',
        description='Publish built-in mock scan packet; software proof only')

    use_sim_time = LaunchConfiguration('use_sim_time')
    serial_port = LaunchConfiguration('serial_port')
    serial_baudrate = LaunchConfiguration('serial_baudrate')
    command_mode = LaunchConfiguration('command_mode')
    track_width_m = LaunchConfiguration('track_width_m')
    max_wheel_speed_mps = LaunchConfiguration('max_wheel_speed_mps')
    waypoint_file = LaunchConfiguration('waypoint_file')
    delivery_mode = LaunchConfiguration('delivery_mode')
    delivery_target = LaunchConfiguration('delivery_target')
    return_target = LaunchConfiguration('return_target')
    elevator_assist_enabled = LaunchConfiguration('elevator_assist_enabled')
    elevator_assist_mode = LaunchConfiguration('elevator_assist_mode')
    elevator_assist_target_floor = LaunchConfiguration('elevator_assist_target_floor')
    elevator_assist_dry_run_failure = LaunchConfiguration('elevator_assist_dry_run_failure')
    task_record_dir = LaunchConfiguration('task_record_dir')
    dropoff_timeout_sec = LaunchConfiguration('dropoff_timeout_sec')
    navigation_timeout_sec = LaunchConfiguration('navigation_timeout_sec')
    operator_gateway = LaunchConfiguration('operator_gateway')
    operator_gateway_host = LaunchConfiguration('operator_gateway_host')
    operator_gateway_port = LaunchConfiguration('operator_gateway_port')
    operator_gateway_collect_action = LaunchConfiguration('operator_gateway_collect_action')
    operator_gateway_dropoff_service = LaunchConfiguration('operator_gateway_dropoff_service')
    operator_status_file = LaunchConfiguration('operator_status_file')
    operator_pose_topic = LaunchConfiguration('operator_pose_topic')
    operator_hardware_proof_ref = LaunchConfiguration('operator_hardware_proof_ref')
    remote_bridge = LaunchConfiguration('remote_bridge')
    remote_cloud_base_url = LaunchConfiguration('remote_cloud_base_url')
    remote_robot_id = LaunchConfiguration('remote_robot_id')
    remote_auth_token = LaunchConfiguration('remote_auth_token')
    remote_poll_interval_sec = LaunchConfiguration('remote_poll_interval_sec')
    remote_request_timeout_sec = LaunchConfiguration('remote_request_timeout_sec')
    lidar_enabled = LaunchConfiguration('lidar_enabled')
    lidar_serial_port = LaunchConfiguration('lidar_serial_port')
    lidar_serial_baudrate = LaunchConfiguration('lidar_serial_baudrate')
    lidar_frame_id = LaunchConfiguration('lidar_frame_id')
    lidar_scan_topic = LaunchConfiguration('lidar_scan_topic')
    lidar_raw_packet_topic = LaunchConfiguration('lidar_raw_packet_topic')
    lidar_publish_raw_packets = LaunchConfiguration('lidar_publish_raw_packets')
    lidar_range_min = LaunchConfiguration('lidar_range_min')
    lidar_range_max = LaunchConfiguration('lidar_range_max')
    lidar_scan_time = LaunchConfiguration('lidar_scan_time')
    lidar_time_increment = LaunchConfiguration('lidar_time_increment')
    lidar_tf_x = LaunchConfiguration('lidar_tf_x')
    lidar_tf_y = LaunchConfiguration('lidar_tf_y')
    lidar_tf_z = LaunchConfiguration('lidar_tf_z')
    lidar_tf_roll = LaunchConfiguration('lidar_tf_roll')
    lidar_tf_pitch = LaunchConfiguration('lidar_tf_pitch')
    lidar_tf_yaw = LaunchConfiguration('lidar_tf_yaw')
    lidar_mock_packets = LaunchConfiguration('lidar_mock_packets')
    lidar_mock_scan = LaunchConfiguration('lidar_mock_scan')
    remote_bridge_condition = IfCondition(remote_bridge)
    lidar_condition = IfCondition(lidar_enabled)

    nodes = [
        # --- Hardware Bridge (ESP32 <-> ROS2) ---
        Node(
            package='ros2_trashbot_hardware',
            executable='esp32_bridge',
            name='esp32_bridge',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'serial_port': serial_port,
                'serial_baudrate': serial_baudrate,
                'command_mode': command_mode,
                'track_width_m': track_width_m,
                'max_wheel_speed_mps': max_wheel_speed_mps,
            }],
        ),

        # --- LiDAR 闭环：默认关闭，避免无串口开发环境阻塞整车 bringup ---
        Node(
            package='ros2_trashbot_nav',
            executable='lidar_driver',
            name='lidar_driver',
            output='screen',
            condition=lidar_condition,
            parameters=[{
                'serial_port': lidar_serial_port,
                'serial_baudrate': lidar_serial_baudrate,
                'frame_id': lidar_frame_id,
                'scan_topic': lidar_scan_topic,
                'raw_packet_topic': lidar_raw_packet_topic,
                'publish_raw_packets': lidar_publish_raw_packets,
                'range_min': lidar_range_min,
                'range_max': lidar_range_max,
                'scan_time': lidar_scan_time,
                'time_increment': lidar_time_increment,
                'mock_packets': lidar_mock_packets,
                'mock_scan': lidar_mock_scan,
            }],
        ),

        # --- LiDAR 占位 TF：默认全零只是软件闭环占位，真实上车必须测量安装位姿 ---
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_laser_frame',
            output='screen',
            condition=lidar_condition,
            arguments=[
                '--x', lidar_tf_x,
                '--y', lidar_tf_y,
                '--z', lidar_tf_z,
                '--roll', lidar_tf_roll,
                '--pitch', lidar_tf_pitch,
                '--yaw', lidar_tf_yaw,
                '--frame-id', 'base_link',
                '--child-frame-id', lidar_frame_id,
            ],
        ),

        # --- Navigation ---
        Node(
            package='ros2_trashbot_nav',
            executable='waypoint_manager',
            name='waypoint_manager',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'waypoint_file': waypoint_file,
            }],
        ),

        Node(
            package='ros2_trashbot_nav',
            executable='map_recorder',
            name='map_recorder',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
            }],
        ),

        # --- Behavior ---
        Node(
            package='ros2_trashbot_behavior',
            executable='task_orchestrator',
            name='task_orchestrator',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'waypoint_file': waypoint_file,
                'delivery_mode': delivery_mode,
                'delivery_target': delivery_target,
                'return_target': return_target,
                'elevator_assist_enabled': elevator_assist_enabled,
                'elevator_assist_mode': elevator_assist_mode,
                'elevator_assist_target_floor': elevator_assist_target_floor,
                'elevator_assist_dry_run_failure': elevator_assist_dry_run_failure,
                'task_record_dir': task_record_dir,
                'dropoff_timeout_sec': dropoff_timeout_sec,
                'navigation_timeout_sec': navigation_timeout_sec,
            }],
        ),

        Node(
            package='ros2_trashbot_behavior',
            executable='operator_gateway',
            name='operator_gateway',
            output='screen',
            condition=IfCondition(operator_gateway),
            parameters=[{
                'use_sim_time': use_sim_time,
                'host': operator_gateway_host,
                'port': operator_gateway_port,
                'default_target': delivery_target,
                'collect_action_name': operator_gateway_collect_action,
                'dropoff_service_name': operator_gateway_dropoff_service,
                'status_file': operator_status_file,
                'pose_topic': operator_pose_topic,
                'hardware_proof_ref': operator_hardware_proof_ref,
            }],
        ),

        Node(
            package='ros2_trashbot_behavior',
            executable='remote_bridge',
            name='remote_bridge',
            output='screen',
            condition=remote_bridge_condition,
            parameters=[{
                'enabled': remote_bridge,
                'cloud_base_url': remote_cloud_base_url,
                'robot_id': remote_robot_id,
                'auth_token': remote_auth_token,
                'poll_interval_sec': remote_poll_interval_sec,
                'request_timeout_sec': remote_request_timeout_sec,
                'collect_action_name': operator_gateway_collect_action,
                'dropoff_service_name': operator_gateway_dropoff_service,
            }],
        ),
    ]

    return LaunchDescription([
        use_sim_time_arg,
        serial_port_arg,
        serial_baudrate_arg,
        command_mode_arg,
        track_width_arg,
        max_wheel_speed_arg,
        waypoint_file_arg,
        delivery_mode_arg,
        delivery_target_arg,
        return_target_arg,
        elevator_assist_enabled_arg,
        elevator_assist_mode_arg,
        elevator_assist_target_floor_arg,
        elevator_assist_dry_run_failure_arg,
        task_record_dir_arg,
        dropoff_timeout_sec_arg,
        navigation_timeout_sec_arg,
        operator_gateway_arg,
        operator_gateway_host_arg,
        operator_gateway_port_arg,
        operator_gateway_collect_action_arg,
        operator_gateway_dropoff_service_arg,
        operator_status_file_arg,
        operator_pose_topic_arg,
        operator_hardware_proof_ref_arg,
        remote_bridge_arg,
        remote_cloud_base_url_arg,
        remote_robot_id_arg,
        remote_auth_token_arg,
        remote_poll_interval_sec_arg,
        remote_request_timeout_sec_arg,
        lidar_enabled_arg,
        lidar_serial_port_arg,
        lidar_serial_baudrate_arg,
        lidar_frame_id_arg,
        lidar_scan_topic_arg,
        lidar_raw_packet_topic_arg,
        lidar_publish_raw_packets_arg,
        lidar_range_min_arg,
        lidar_range_max_arg,
        lidar_scan_time_arg,
        lidar_time_increment_arg,
        lidar_tf_x_arg,
        lidar_tf_y_arg,
        lidar_tf_z_arg,
        lidar_tf_roll_arg,
        lidar_tf_pitch_arg,
        lidar_tf_yaw_arg,
        lidar_mock_packets_arg,
        lidar_mock_scan_arg,
        *nodes,
    ])
