"""Main bringup launch - starts all trashbot nodes together."""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # Arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock')

    map_file_arg = DeclareLaunchArgument(
        'map_file', default_value='',
        description='Path to saved map YAML (empty = learn mode)')

    camera_topic_arg = DeclareLaunchArgument(
        'camera_topic', default_value='/camera/image_raw',
        description='Camera image topic')

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_file = LaunchConfiguration('map_file')
    camera_topic = LaunchConfiguration('camera_topic')

    trashbot_nav_dir = FindPackageShare('ros2_trashbot_nav')
    trashbot_vision_dir = FindPackageShare('ros2_trashbot_vision')
    trashbot_behavior_dir = FindPackageShare('ros2_trashbot_behavior')

    nodes = [
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

        # --- Navigation ---
        Node(
            package='ros2_trashbot_nav',
            executable='waypoint_manager',
            name='waypoint_manager',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
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

        # --- Vision ---
        Node(
            package='ros2_trashbot_vision',
            executable='trash_detector',
            name='trash_detector',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'camera_topic': camera_topic,
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
            }],
        ),

        # --- Nav2 (conditional on map) ---
        # IncludeLaunchDescription(
        #     PythonLaunchDescriptionSource(
        #         os.path.join(FindPackageShare('nav2_bringup').perform(None), 'launch', 'bringup_launch.py')),
        #     launch_arguments={
        #         'map': map_file,
        #         'use_sim_time': use_sim_time,
        #     }.items(),
        # ),
    ]

    # SLAM in learning mode (no map provided)
    # slam_launch = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(
    #         os.path.join(FindPackageShare('slam_toolbox').perform(None), 'launch', 'online_async_launch.py')),
    #     launch_arguments={'use_sim_time': use_sim_time}.items(),
    # )

    return LaunchDescription([
        use_sim_time_arg,
        map_file_arg,
        camera_topic_arg,
        *nodes,
    ])
