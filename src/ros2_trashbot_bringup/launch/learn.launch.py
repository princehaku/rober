"""Learning phase launch - SLAM + manual drive recording."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock')

    record_interval_arg = DeclareLaunchArgument(
        'record_interval', default_value='5.0',
        description='Seconds between automatic waypoint recording during learning')

    pose_topic_arg = DeclareLaunchArgument(
        'pose_topic', default_value='/pose',
        description='PoseWithCovarianceStamped topic used for recording waypoints')

    route_recorder_arg = DeclareLaunchArgument(
        'route_recorder', default_value='false',
        description='Start fixed-route CSV and keyframe recording during manual learning')

    route_output_dir_arg = DeclareLaunchArgument(
        'route_output_dir',
        default_value=PathJoinSubstitution([
            EnvironmentVariable('HOME'),
            '.ros',
            'trashbot_runs',
            'run_001',
        ]),
        description='Directory for learned route.csv and keyframes')

    route_camera_topic_arg = DeclareLaunchArgument(
        'route_camera_topic', default_value='/camera/image_raw',
        description='Camera Image topic used for route keyframe capture')

    route_odom_topic_arg = DeclareLaunchArgument(
        'route_odom_topic', default_value='/odom',
        description='Odometry topic used for fixed-route pose capture')

    route_min_distance_m_arg = DeclareLaunchArgument(
        'route_min_distance_m', default_value='0.8',
        description='Minimum travel distance between recorded fixed-route checkpoints')

    route_frame_id_arg = DeclareLaunchArgument(
        'route_frame_id', default_value='map',
        description='Frame id written to learned fixed-route CSV checkpoints')

    use_sim_time = LaunchConfiguration('use_sim_time')
    record_interval = LaunchConfiguration('record_interval')
    pose_topic = LaunchConfiguration('pose_topic')
    route_recorder = LaunchConfiguration('route_recorder')
    route_output_dir = LaunchConfiguration('route_output_dir')
    route_camera_topic = LaunchConfiguration('route_camera_topic')
    route_odom_topic = LaunchConfiguration('route_odom_topic')
    route_min_distance_m = LaunchConfiguration('route_min_distance_m')
    route_frame_id = LaunchConfiguration('route_frame_id')

    return LaunchDescription([
        use_sim_time_arg,
        record_interval_arg,
        pose_topic_arg,
        route_recorder_arg,
        route_output_dir_arg,
        route_camera_topic_arg,
        route_odom_topic_arg,
        route_min_distance_m_arg,
        route_frame_id_arg,

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
                'pose_topic': pose_topic,
            }],
        ),

        # Optional fixed-route CSV/keyframe recorder for repeatable delivery runs.
        Node(
            package='ros2_trashbot_nav',
            executable='route_data_recorder',
            name='route_data_recorder',
            output='screen',
            condition=IfCondition(route_recorder),
            parameters=[{
                'use_sim_time': use_sim_time,
                'output_dir': route_output_dir,
                'camera_topic': route_camera_topic,
                'odom_topic': route_odom_topic,
                'min_distance_m': route_min_distance_m,
                'route_frame_id': route_frame_id,
            }],
        ),
    ])
