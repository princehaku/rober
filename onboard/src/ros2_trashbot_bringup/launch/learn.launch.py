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

    route_id_arg = DeclareLaunchArgument(
        'route_id', default_value='',
        description='Route id written to learned keyframe sample manifest context')

    route_sample_manifest_name_arg = DeclareLaunchArgument(
        'route_sample_manifest_name', default_value='manifest.json',
        description='Vision sample manifest filename written beside learned route data')

    route_sample_manifest_max_entries_arg = DeclareLaunchArgument(
        'route_sample_manifest_max_entries', default_value='500',
        description='Maximum learned keyframe sample entries kept in the route manifest')

    lidar_enabled_arg = DeclareLaunchArgument(
        'lidar_enabled', default_value='false',
        description='Start ROS2 LiDAR driver during learning; default false keeps mock/offline learning usable')

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
        description='LaserScan topic consumed by SLAM during learning')

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
    record_interval = LaunchConfiguration('record_interval')
    pose_topic = LaunchConfiguration('pose_topic')
    route_recorder = LaunchConfiguration('route_recorder')
    route_output_dir = LaunchConfiguration('route_output_dir')
    route_camera_topic = LaunchConfiguration('route_camera_topic')
    route_odom_topic = LaunchConfiguration('route_odom_topic')
    route_min_distance_m = LaunchConfiguration('route_min_distance_m')
    route_frame_id = LaunchConfiguration('route_frame_id')
    route_id = LaunchConfiguration('route_id')
    route_sample_manifest_name = LaunchConfiguration('route_sample_manifest_name')
    route_sample_manifest_max_entries = LaunchConfiguration('route_sample_manifest_max_entries')
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
    lidar_condition = IfCondition(lidar_enabled)

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
        route_id_arg,
        route_sample_manifest_name_arg,
        route_sample_manifest_max_entries_arg,
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

        # LiDAR 闭环默认关闭，避免没有真实 USB 串口时阻塞人工学习和路线记录。
        Node(
            package='ros2_trashbot_hardware',
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

        # TF 与 LiDAR 同 gate，防止未接雷达时向 SLAM 暴露误导性的 laser_frame。
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

        # SLAM Toolbox 只消费 launch 提供的话题/TF；LiDAR 未开启时不假装有 scan 输入。
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

        # 地图记录保持独立，便于先用 mock/仿真验证学习流程，再切换真实 LiDAR。
        Node(
            package='ros2_trashbot_nav',
            executable='map_recorder',
            name='map_recorder',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),

        # 航点学习仍以 pose_topic 为契约，避免和具体定位来源强耦合。
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

        # 固定路线记录是可选能力，显式开启后才写路线和关键帧样本。
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
                'route_id': route_id,
                'sample_manifest_name': route_sample_manifest_name,
                'sample_manifest_max_entries': route_sample_manifest_max_entries,
            }],
        ),
    ])
