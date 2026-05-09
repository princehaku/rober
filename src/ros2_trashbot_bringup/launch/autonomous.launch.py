"""Autonomous mode launch - patrol, collect, deliver."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
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
        'enable_visual_gate', default_value='true',
        description='Enable keyframe visual gate for fixed-route checkpoints')

    visual_match_threshold_arg = DeclareLaunchArgument(
        'visual_match_threshold', default_value='25',
        description='Minimum ORB matches required by the fixed-route visual gate')

    fixed_route_dry_run_arg = DeclareLaunchArgument(
        'fixed_route_dry_run', default_value='true',
        description='Run fixed-route checkpoints without creating Nav2 BasicNavigator')

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
        'command_mode', default_value='speed',
        description='WAVE ROVER command mode: speed uses T=1, ros uses T=13')

    track_width_arg = DeclareLaunchArgument(
        'track_width_m', default_value='0.172',
        description='WAVE ROVER differential drive track width in meters')

    max_wheel_speed_arg = DeclareLaunchArgument(
        'max_wheel_speed_mps', default_value='1.3',
        description='Wheel speed used to normalize T=1 speed commands')

    delivery_mode_arg = DeclareLaunchArgument(
        'delivery_mode', default_value='dry_run',
        description='Delivery mode: dry_run, waypoint, or fixed_route')

    delivery_target_arg = DeclareLaunchArgument(
        'delivery_target', default_value='trash_station',
        description='Waypoint name for trash station delivery')

    return_target_arg = DeclareLaunchArgument(
        'return_target', default_value='',
        description='Optional waypoint name to return to after dropoff')

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_file = LaunchConfiguration('map_file')
    waypoint_file = LaunchConfiguration('waypoint_file')
    navigation_mode = LaunchConfiguration('navigation_mode')
    route_file = LaunchConfiguration('route_file')
    keyframe_dir = LaunchConfiguration('keyframe_dir')
    enable_visual_gate = LaunchConfiguration('enable_visual_gate')
    visual_match_threshold = LaunchConfiguration('visual_match_threshold')
    fixed_route_dry_run = LaunchConfiguration('fixed_route_dry_run')
    debug_status_file = LaunchConfiguration('debug_status_file')
    route_debug_web = LaunchConfiguration('route_debug_web')
    operator_gateway = LaunchConfiguration('operator_gateway')
    operator_gateway_host = LaunchConfiguration('operator_gateway_host')
    operator_gateway_port = LaunchConfiguration('operator_gateway_port')
    operator_gateway_collect_action = LaunchConfiguration('operator_gateway_collect_action')
    operator_gateway_dropoff_service = LaunchConfiguration('operator_gateway_dropoff_service')
    operator_status_file = LaunchConfiguration('operator_status_file')
    operator_pose_topic = LaunchConfiguration('operator_pose_topic')
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
    delivery_mode = LaunchConfiguration('delivery_mode')
    delivery_target = LaunchConfiguration('delivery_target')
    return_target = LaunchConfiguration('return_target')
    nav2_params_file = PathJoinSubstitution([
        FindPackageShare('ros2_trashbot_nav'),
        'config',
        'nav2_params.yaml',
    ])
    fixed_route_expression = PythonExpression([
        "'", navigation_mode, "' == 'fixed_route' or '", delivery_mode, "' == 'fixed_route'"
    ])
    fixed_route_condition = IfCondition(fixed_route_expression)
    waypoint_condition = UnlessCondition(fixed_route_expression)
    route_debug_web_condition = IfCondition(PythonExpression([
        "('", navigation_mode, "' == 'fixed_route' or '", delivery_mode,
        "' == 'fixed_route') and '", route_debug_web, "' == 'true'"
    ]))
    operator_gateway_condition = IfCondition(operator_gateway)
    remote_bridge_condition = IfCondition(remote_bridge)

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
        debug_status_file_arg,
        route_debug_web_arg,
        operator_gateway_arg,
        operator_gateway_host_arg,
        operator_gateway_port_arg,
        operator_gateway_collect_action_arg,
        operator_gateway_dropoff_service_arg,
        operator_status_file_arg,
        operator_pose_topic_arg,
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
        delivery_mode_arg,
        delivery_target_arg,
        return_target_arg,

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

        # Trash detector
        Node(
            package='ros2_trashbot_vision',
            executable='trash_detector',
            name='trash_detector',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),

        # Task orchestrator
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
                'fixed_route_status_file': debug_status_file,
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
