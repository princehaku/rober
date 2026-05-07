"""Autonomous mode launch - patrol, collect, deliver."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock')

    map_file_arg = DeclareLaunchArgument(
        'map_file',
        default_value='~/.ros/trashbot_maps/trashbot_map.yaml',
        description='Path to saved map')

    patrol_interval_arg = DeclareLaunchArgument(
        'patrol_interval', default_value='300',
        description='Seconds between patrol cycles')

    waypoint_file_arg = DeclareLaunchArgument(
        'waypoint_file',
        default_value='~/.ros/trashbot_maps/waypoints.yaml',
        description='Path to saved waypoint YAML')

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_file = LaunchConfiguration('map_file')
    waypoint_file = LaunchConfiguration('waypoint_file')
    nav2_params_file = PathJoinSubstitution([
        FindPackageShare('ros2_trashbot_nav'),
        'config',
        'nav2_params.yaml',
    ])

    return LaunchDescription([
        use_sim_time_arg,
        map_file_arg,
        patrol_interval_arg,
        waypoint_file_arg,

        # --- Hardware Bridge (ESP32 <-> ROS2) ---
        Node(
            package='ros2_trashbot_hardware',
            executable='esp32_bridge',
            name='esp32_bridge',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'port': '/dev/ttyUSB0',
                'baudrate': 115200,
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
            parameters=[{'use_sim_time': use_sim_time}],
        ),

        # Patrol scheduler (periodic patrol)
        Node(
            package='ros2_trashbot_nav',
            executable='nav_to_goal',
            name='nav_to_goal',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),
    ])
