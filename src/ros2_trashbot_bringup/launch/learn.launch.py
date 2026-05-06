"""Learning phase launch - SLAM + manual drive recording."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock')

    record_interval_arg = DeclareLaunchArgument(
        'record_interval', default_value='5.0',
        description='Seconds between automatic waypoint recording during learning')

    use_sim_time = LaunchConfiguration('use_sim_time')
    record_interval = LaunchConfiguration('record_interval')

    return LaunchDescription([
        use_sim_time_arg,
        record_interval_arg,

        # SLAM Toolbox for mapping
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'mode': 'mapping',
            }],
        ),

        # Map recorder
        Node(
            package='ros2_trashbot_nav',
            executable='map_recorder',
            name='map_recorder',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),

        # Waypoint manager (learning mode)
        Node(
            package='ros2_trashbot_nav',
            executable='waypoint_manager',
            name='waypoint_manager',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'learn_mode': True,
                'record_interval': record_interval,
            }],
        ),

        # Trash detector (recording detections during learning)
        Node(
            package='ros2_trashbot_vision',
            executable='trash_detector',
            name='trash_detector',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),
    ])
