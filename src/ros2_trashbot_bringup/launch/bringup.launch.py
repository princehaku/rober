"""Main bringup launch - starts all trashbot nodes together."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock')

    camera_topic_arg = DeclareLaunchArgument(
        'camera_topic', default_value='/camera/image_raw',
        description='Camera image topic')

    use_sim_time = LaunchConfiguration('use_sim_time')
    camera_topic = LaunchConfiguration('camera_topic')

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
    ]

    return LaunchDescription([
        use_sim_time_arg,
        camera_topic_arg,
        *nodes,
    ])
