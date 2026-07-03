"""Autonomous mode launch - patrol, collect, deliver."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch.substitutions import PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock')

    map_file_arg = DeclareLaunchArgument(
        'map_file',
        default_value=PathJoinSubstitution([
            EnvironmentVariable('HOME'),
            '.ros',
            'trashbot_maps',
            'trashbot_map.yaml',
        ]),
        description='Path to saved map')

    waypoint_file_arg = DeclareLaunchArgument(
        'waypoint_file',
        default_value=PathJoinSubstitution([
            EnvironmentVariable('HOME'),
            '.ros',
            'trashbot_maps',
            'waypoints.yaml',
        ]),
        description='Path to saved waypoint YAML')

    navigation_mode_arg = DeclareLaunchArgument(
        'navigation_mode', default_value='waypoint',
        description='Navigation controller: waypoint or fixed_route')

    route_file_arg = DeclareLaunchArgument(
        'route_file',
        default_value=PathJoinSubstitution([
            EnvironmentVariable('HOME'),
            '.ros',
            'trashbot_maps',
            'fixed_route.yaml',
        ]),
        description='Fixed-route YAML or CSV route file')

    keyframe_dir_arg = DeclareLaunchArgument(
        'keyframe_dir',
        default_value=PathJoinSubstitution([
            EnvironmentVariable('HOME'),
            '.ros',
            'trashbot_maps',
            'keyframes',
        ]),
        description='Fixed-route visual keyframe directory')

    enable_visual_gate_arg = DeclareLaunchArgument(
        'enable_visual_gate', default_value='false',
        description='Enable keyframe visual gate for fixed-route checkpoints')

    visual_match_threshold_arg = DeclareLaunchArgument(
        'visual_match_threshold', default_value='25',
        description='Minimum ORB matches required by the fixed-route visual gate')

    fixed_route_dry_run_arg = DeclareLaunchArgument(
        'fixed_route_dry_run', default_value='false',
        description='Run fixed-route checkpoints without creating Nav2 BasicNavigator')

    nav2_stack_only_arg = DeclareLaunchArgument(
        'nav2_stack_only', default_value='false',
        description='Start only ESP32 bridge and Nav2 bringup; skip patrol/task nodes')

    base_enabled_arg = DeclareLaunchArgument(
        'base_enabled', default_value='true',
        description='Start the ESP32 bridge; disable when an existing bridge already owns the base UART')

    lidar_enabled_arg = DeclareLaunchArgument(
        'lidar_enabled', default_value='false',
        description='Start the LiDAR driver for Nav2 /scan input when the serial device is available')

    lidar_serial_port_arg = DeclareLaunchArgument(
        'lidar_serial_port', default_value='/dev/ttyACM0',
        description='LiDAR serial port used by ros2_trashbot_hardware/lidar_driver')

    lidar_serial_baudrate_arg = DeclareLaunchArgument(
        'lidar_serial_baudrate', default_value='230400',
        description='LiDAR serial baudrate used by ros2_trashbot_hardware/lidar_driver')

    lidar_frame_id_arg = DeclareLaunchArgument(
        'lidar_frame_id', default_value='laser_frame',
        description='frame_id attached to LiDAR LaserScan messages')

    lidar_scan_topic_arg = DeclareLaunchArgument(
        'lidar_scan_topic', default_value='/scan',
        description='Topic published by the LiDAR driver and consumed by Nav2/AMCL')

    lidar_raw_packet_topic_arg = DeclareLaunchArgument(
        'lidar_raw_packet_topic', default_value='/lidar/raw_packet',
        description='Optional LiDAR raw packet topic for packet-level debugging')

    lidar_publish_raw_packets_arg = DeclareLaunchArgument(
        'lidar_publish_raw_packets', default_value='false',
        description='Publish raw LiDAR packets when packet-level debugging is needed')

    lidar_mock_packets_arg = DeclareLaunchArgument(
        'lidar_mock_packets', default_value='',
        description='Optional hex packet replay input; keeps LiDAR driver in mock mode')

    lidar_mock_scan_arg = DeclareLaunchArgument(
        'lidar_mock_scan', default_value='false',
        description='Publish deterministic mock LiDAR scans without opening a serial port')

    static_laser_tf_enabled_arg = DeclareLaunchArgument(
        'static_laser_tf_enabled', default_value='false',
        description='Publish a smoke-only base_link -> laser_frame static TF; not a mechanical calibration')

    base_frame_id_arg = DeclareLaunchArgument(
        'base_frame_id', default_value='base_link',
        description='Parent frame used by the smoke-only static laser TF')

    laser_tf_x_arg = DeclareLaunchArgument(
        'laser_tf_x', default_value='0.0',
        description='Smoke-only static TF x offset from base_frame_id to lidar_frame_id')

    laser_tf_y_arg = DeclareLaunchArgument(
        'laser_tf_y', default_value='0.0',
        description='Smoke-only static TF y offset from base_frame_id to lidar_frame_id')

    laser_tf_z_arg = DeclareLaunchArgument(
        'laser_tf_z', default_value='0.0',
        description='Smoke-only static TF z offset from base_frame_id to lidar_frame_id')

    laser_tf_roll_arg = DeclareLaunchArgument(
        'laser_tf_roll', default_value='0.0',
        description='Smoke-only static TF roll from base_frame_id to lidar_frame_id')

    laser_tf_pitch_arg = DeclareLaunchArgument(
        'laser_tf_pitch', default_value='0.0',
        description='Smoke-only static TF pitch from base_frame_id to lidar_frame_id')

    laser_tf_yaw_arg = DeclareLaunchArgument(
        'laser_tf_yaw', default_value='0.0',
        description='Smoke-only static TF yaw from base_frame_id to lidar_frame_id')

    debug_status_file_arg = DeclareLaunchArgument(
        'debug_status_file', default_value='/tmp/trashbot_fixed_route_status.json',
        description='Path to fixed-route debug status JSON')

    route_debug_web_arg = DeclareLaunchArgument(
        'route_debug_web', default_value='false',
        description='Start fixed-route debug web status page')

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

    serial_port_arg = DeclareLaunchArgument(
        'serial_port', default_value='/dev/ttyUSB0',
        description='UART device for the WAVE ROVER ESP32 controller')

    serial_baudrate_arg = DeclareLaunchArgument(
        'serial_baudrate', default_value='115200',
        description='UART baud rate for the WAVE ROVER ESP32 controller')

    command_mode_arg = DeclareLaunchArgument(
        'command_mode', default_value='pwm',
        description='WAVE ROVER command mode: pwm keeps ROS /cmd_vel as the control surface and maps to vendor T=11 PWM; ros/T=13 and speed/T=1 remain explicit diagnostics')

    track_width_arg = DeclareLaunchArgument(
        'track_width_m', default_value='0.172',
        description='WAVE ROVER differential drive track width in meters')

    max_wheel_speed_arg = DeclareLaunchArgument(
        'max_wheel_speed_mps', default_value='1.3',
        description='Wheel speed used to normalize T=1 speed or T=11 PWM commands')

    pwm_min_abs_arg = DeclareLaunchArgument(
        'pwm_min_abs', default_value='164',
        description='Minimum nonzero PWM for WAVE ROVER T=11 mode; vendor sample and 2026-07-03 field smoke use 164')

    pwm_max_abs_arg = DeclareLaunchArgument(
        'pwm_max_abs', default_value='164',
        description='Maximum PWM for WAVE ROVER T=11 low-speed mode')

    command_transport_arg = DeclareLaunchArgument(
        'command_transport', default_value='http',
        description='Current field default uses ESP32 HTTP /js control; override to serial only after UART TX is verified')

    wave_rover_http_base_url_arg = DeclareLaunchArgument(
        'wave_rover_http_base_url', default_value='http://192.168.1.3',
        description='Fixed ESP32 HTTP base URL for the current WAVE ROVER control path')

    http_timeout_s_arg = DeclareLaunchArgument(
        'http_timeout_s', default_value='0.6',
        description='HTTP command timeout for the ESP32 /js control path')

    main_type_arg = DeclareLaunchArgument(
        'main_type', default_value='1',
        description='Vendor T=900 main type: 1 is WAVE ROVER; 2 is UGV02 and must not be the default for this robot')

    module_type_arg = DeclareLaunchArgument(
        'module_type', default_value='0',
        description='Vendor T=900 module type for this WAVE ROVER chassis')

    delivery_mode_arg = DeclareLaunchArgument(
        'delivery_mode', default_value='dry_run',
        description='Delivery mode: dry_run, waypoint, or fixed_route')

    delivery_target_arg = DeclareLaunchArgument(
        'delivery_target', default_value='trash_station',
        description='Waypoint name for trash station delivery')

    return_target_arg = DeclareLaunchArgument(
        'return_target', default_value='',
        description='Optional waypoint name to return to after dropoff')

    elevator_assist_enabled_arg = DeclareLaunchArgument(
        'elevator_assist_enabled', default_value='true',
        description=(
            'Enable elevator assisted delivery dry-run as the default software proof mainline; '
            'not real elevator, not real TTS/speaker, not real Nav2/fixed-route, not HIL'))

    elevator_assist_mode_arg = DeclareLaunchArgument(
        'elevator_assist_mode', default_value='dry_run',
        description='Elevator assisted delivery mode; dry_run is the only software-only mode')

    elevator_assist_target_floor_arg = DeclareLaunchArgument(
        'elevator_assist_target_floor', default_value='1',
        description='Target floor used in elevator assisted delivery dry-run records')

    elevator_assist_dry_run_failure_arg = DeclareLaunchArgument(
        'elevator_assist_dry_run_failure', default_value='',
        description='Optional dry-run failure: door_timeout, target_floor_unconfirmed, unsafe_to_exit')

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_file = LaunchConfiguration('map_file')
    waypoint_file = LaunchConfiguration('waypoint_file')
    navigation_mode = LaunchConfiguration('navigation_mode')
    route_file = LaunchConfiguration('route_file')
    keyframe_dir = LaunchConfiguration('keyframe_dir')
    enable_visual_gate = LaunchConfiguration('enable_visual_gate')
    visual_match_threshold = LaunchConfiguration('visual_match_threshold')
    fixed_route_dry_run = LaunchConfiguration('fixed_route_dry_run')
    nav2_stack_only = LaunchConfiguration('nav2_stack_only')
    base_enabled = LaunchConfiguration('base_enabled')
    lidar_enabled = LaunchConfiguration('lidar_enabled')
    lidar_serial_port = LaunchConfiguration('lidar_serial_port')
    lidar_serial_baudrate = LaunchConfiguration('lidar_serial_baudrate')
    lidar_frame_id = LaunchConfiguration('lidar_frame_id')
    lidar_scan_topic = LaunchConfiguration('lidar_scan_topic')
    lidar_raw_packet_topic = LaunchConfiguration('lidar_raw_packet_topic')
    lidar_publish_raw_packets = LaunchConfiguration('lidar_publish_raw_packets')
    lidar_mock_packets = LaunchConfiguration('lidar_mock_packets')
    lidar_mock_scan = LaunchConfiguration('lidar_mock_scan')
    static_laser_tf_enabled = LaunchConfiguration('static_laser_tf_enabled')
    base_frame_id = LaunchConfiguration('base_frame_id')
    laser_tf_x = LaunchConfiguration('laser_tf_x')
    laser_tf_y = LaunchConfiguration('laser_tf_y')
    laser_tf_z = LaunchConfiguration('laser_tf_z')
    laser_tf_roll = LaunchConfiguration('laser_tf_roll')
    laser_tf_pitch = LaunchConfiguration('laser_tf_pitch')
    laser_tf_yaw = LaunchConfiguration('laser_tf_yaw')
    debug_status_file = LaunchConfiguration('debug_status_file')
    route_debug_web = LaunchConfiguration('route_debug_web')
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
    serial_port = LaunchConfiguration('serial_port')
    serial_baudrate = LaunchConfiguration('serial_baudrate')
    command_mode = LaunchConfiguration('command_mode')
    track_width_m = LaunchConfiguration('track_width_m')
    max_wheel_speed_mps = LaunchConfiguration('max_wheel_speed_mps')
    pwm_min_abs = LaunchConfiguration('pwm_min_abs')
    pwm_max_abs = LaunchConfiguration('pwm_max_abs')
    command_transport = LaunchConfiguration('command_transport')
    wave_rover_http_base_url = LaunchConfiguration('wave_rover_http_base_url')
    http_timeout_s = LaunchConfiguration('http_timeout_s')
    main_type = LaunchConfiguration('main_type')
    module_type = LaunchConfiguration('module_type')
    delivery_mode = LaunchConfiguration('delivery_mode')
    delivery_target = LaunchConfiguration('delivery_target')
    return_target = LaunchConfiguration('return_target')
    elevator_assist_enabled = LaunchConfiguration('elevator_assist_enabled')
    elevator_assist_mode = LaunchConfiguration('elevator_assist_mode')
    elevator_assist_target_floor = LaunchConfiguration('elevator_assist_target_floor')
    elevator_assist_dry_run_failure = LaunchConfiguration('elevator_assist_dry_run_failure')
    nav2_params_file = PathJoinSubstitution([
        FindPackageShare('ros2_trashbot_nav'),
        'config',
        'nav2_params.yaml',
    ])
    full_fixed_route_expression = PythonExpression([
        "'", nav2_stack_only, "'.lower() != 'true' and ('",
        navigation_mode, "' == 'fixed_route' or '", delivery_mode, "' == 'fixed_route')"
    ])
    full_waypoint_expression = PythonExpression([
        "'", nav2_stack_only, "'.lower() != 'true' and not ('",
        navigation_mode, "' == 'fixed_route' or '", delivery_mode, "' == 'fixed_route')"
    ])
    full_stack_expression = PythonExpression(["'", nav2_stack_only, "'.lower() != 'true'"])
    fixed_route_condition = IfCondition(full_fixed_route_expression)
    waypoint_condition = IfCondition(full_waypoint_expression)
    full_stack_condition = IfCondition(full_stack_expression)
    route_debug_web_condition = IfCondition(PythonExpression([
        "'", nav2_stack_only, "'.lower() != 'true' and ('", navigation_mode, "' == 'fixed_route' or '", delivery_mode,
        "' == 'fixed_route') and '", route_debug_web, "' == 'true'"
    ]))
    operator_gateway_condition = IfCondition(PythonExpression([
        "'", nav2_stack_only, "'.lower() != 'true' and '", operator_gateway, "'.lower() == 'true'"
    ]))
    remote_bridge_condition = IfCondition(PythonExpression([
        "'", nav2_stack_only, "'.lower() != 'true' and '", remote_bridge, "'.lower() == 'true'"
    ]))

    return LaunchDescription([
        use_sim_time_arg,
        map_file_arg,
        waypoint_file_arg,
        navigation_mode_arg,
        route_file_arg,
        keyframe_dir_arg,
        enable_visual_gate_arg,
        visual_match_threshold_arg,
        fixed_route_dry_run_arg,
        nav2_stack_only_arg,
        base_enabled_arg,
        lidar_enabled_arg,
        lidar_serial_port_arg,
        lidar_serial_baudrate_arg,
        lidar_frame_id_arg,
        lidar_scan_topic_arg,
        lidar_raw_packet_topic_arg,
        lidar_publish_raw_packets_arg,
        lidar_mock_packets_arg,
        lidar_mock_scan_arg,
        static_laser_tf_enabled_arg,
        base_frame_id_arg,
        laser_tf_x_arg,
        laser_tf_y_arg,
        laser_tf_z_arg,
        laser_tf_roll_arg,
        laser_tf_pitch_arg,
        laser_tf_yaw_arg,
        debug_status_file_arg,
        route_debug_web_arg,
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
        serial_port_arg,
        serial_baudrate_arg,
        command_mode_arg,
        track_width_arg,
        max_wheel_speed_arg,
        pwm_min_abs_arg,
        pwm_max_abs_arg,
        command_transport_arg,
        wave_rover_http_base_url_arg,
        http_timeout_s_arg,
        main_type_arg,
        module_type_arg,
        delivery_mode_arg,
        delivery_target_arg,
        return_target_arg,
        elevator_assist_enabled_arg,
        elevator_assist_mode_arg,
        elevator_assist_target_floor_arg,
        elevator_assist_dry_run_failure_arg,
        # --- Hardware Bridge (ESP32 <-> ROS2) ---
        Node(
            package='ros2_trashbot_hardware',
            executable='esp32_bridge',
            name='esp32_bridge',
            output='screen',
            condition=IfCondition(base_enabled),
            parameters=[{
                'use_sim_time': use_sim_time,
                'serial_port': serial_port,
                'serial_baudrate': serial_baudrate,
                'command_mode': command_mode,
                'track_width_m': track_width_m,
                'max_wheel_speed_mps': max_wheel_speed_mps,
                'pwm_min_abs': pwm_min_abs,
                'pwm_max_abs': pwm_max_abs,
                'command_transport': command_transport,
                'wave_rover_http_base_url': wave_rover_http_base_url,
                'http_timeout_s': http_timeout_s,
                'main_type': main_type,
                'module_type': module_type,
            }],
        ),

        # LiDAR 是 Nav2/AMCL 的 /scan 输入；默认关闭，PC lifecycle 按现场资源自动打开或复用。
        Node(
            package='ros2_trashbot_hardware',
            executable='lidar_driver',
            name='lidar_driver',
            output='screen',
            condition=IfCondition(lidar_enabled),
            parameters=[{
                'serial_port': lidar_serial_port,
                'serial_baudrate': lidar_serial_baudrate,
                'frame_id': lidar_frame_id,
                'scan_topic': lidar_scan_topic,
                'raw_packet_topic': lidar_raw_packet_topic,
                'publish_raw_packets': lidar_publish_raw_packets,
                'mock_packets': lidar_mock_packets,
                'mock_scan': lidar_mock_scan,
            }],
        ),

        # 该 TF 只补齐 Nav2 传感器拓扑，不代表 LiDAR 机械安装已标定。
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_laser_tf',
            output='screen',
            condition=IfCondition(static_laser_tf_enabled),
            arguments=[
                laser_tf_x,
                laser_tf_y,
                laser_tf_z,
                laser_tf_yaw,
                laser_tf_pitch,
                laser_tf_roll,
                base_frame_id,
                lidar_frame_id,
            ],
        ),

        # Nav2 bringup with saved map
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('nav2_bringup'), '/launch/bringup_launch.py'
            ]),
            launch_arguments={
                'map': map_file,
                'use_sim_time': use_sim_time,
                'params_file': nav2_params_file,
            }.items(),
        ),

        # Waypoint manager (autonomous mode)
        Node(
            package='ros2_trashbot_nav',
            executable='waypoint_manager',
            name='waypoint_manager',
            output='screen',
            condition=waypoint_condition,
            parameters=[{
                'use_sim_time': use_sim_time,
                'waypoint_file': waypoint_file,
            }],
        ),

        # Task orchestrator
        Node(
            package='ros2_trashbot_behavior',
            executable='task_orchestrator',
            name='task_orchestrator',
            output='screen',
            condition=full_stack_condition,
            parameters=[{
                'use_sim_time': use_sim_time,
                'waypoint_file': waypoint_file,
                'delivery_mode': delivery_mode,
                'delivery_target': delivery_target,
                'return_target': return_target,
                'fixed_route_status_file': debug_status_file,
                'elevator_assist_enabled': elevator_assist_enabled,
                'elevator_assist_mode': elevator_assist_mode,
                'elevator_assist_target_floor': elevator_assist_target_floor,
                'elevator_assist_dry_run_failure': elevator_assist_dry_run_failure,
            }],
        ),

        # Patrol scheduler (periodic patrol)
        Node(
            package='ros2_trashbot_nav',
            executable='nav_to_goal',
            name='nav_to_goal',
            output='screen',
            condition=waypoint_condition,
            parameters=[{'use_sim_time': use_sim_time}],
        ),

        # Fixed-route runner (mutually exclusive with waypoint patrol control)
        Node(
            package='ros2_trashbot_nav',
            executable='fixed_route_autonomy',
            name='fixed_route_autonomy',
            output='screen',
            condition=fixed_route_condition,
            parameters=[{
                'use_sim_time': use_sim_time,
                'route_file': route_file,
                'keyframe_dir': keyframe_dir,
                'enable_visual_gate': enable_visual_gate,
                'visual_match_threshold': visual_match_threshold,
                'dry_run': fixed_route_dry_run,
                'debug_status_file': debug_status_file,
            }],
        ),

        Node(
            package='ros2_trashbot_nav',
            executable='route_debug_web',
            name='route_debug_web',
            output='screen',
            condition=route_debug_web_condition,
            additional_env={'TRASHBOT_STATUS_FILE': debug_status_file},
        ),

        Node(
            package='ros2_trashbot_behavior',
            executable='operator_gateway',
            name='operator_gateway',
            output='screen',
            condition=operator_gateway_condition,
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
    ])
