"""Learning phase launch - SLAM + manual drive recording."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    # 正常学习模式仍然只启动 SLAM、地图记录和航点学习；下面的传感器参数默认关闭，避免开发机无设备时误报回归。
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

    waypoint_manager_arg = DeclareLaunchArgument(
        'waypoint_manager', default_value='true',
        description='Start waypoint manager during manual learning')

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

    camera_enabled_arg = DeclareLaunchArgument(
        'camera_enabled', default_value='false',
        description='Start the camera publisher for field route keyframe capture')

    camera_device_arg = DeclareLaunchArgument(
        'camera_device', default_value='/dev/video1',
        description='VideoCapture device path or index for the camera publisher')

    camera_topic_arg = DeclareLaunchArgument(
        'camera_topic', default_value='/camera/image_raw',
        description='Topic published by the camera publisher')

    camera_frame_id_arg = DeclareLaunchArgument(
        'camera_frame_id', default_value='camera',
        description='frame_id attached to published camera images')

    camera_width_arg = DeclareLaunchArgument(
        'camera_width', default_value='640',
        description='Requested camera frame width passed to VideoCapture')

    camera_height_arg = DeclareLaunchArgument(
        'camera_height', default_value='480',
        description='Requested camera frame height passed to VideoCapture')

    camera_fps_arg = DeclareLaunchArgument(
        'camera_fps', default_value='15.0',
        description='Requested camera publish rate in frames per second')

    lidar_enabled_arg = DeclareLaunchArgument(
        'lidar_enabled', default_value='false',
        description='Start the LiDAR driver for /scan during field learn capture')

    lidar_serial_port_arg = DeclareLaunchArgument(
        'lidar_serial_port', default_value='/dev/ttyACM0',
        description='LiDAR serial port used by ros2_trashbot_hardware/lidar_driver')

    lidar_serial_baudrate_arg = DeclareLaunchArgument(
        'lidar_serial_baudrate', default_value='150000',
        description='LiDAR serial baudrate used by ros2_trashbot_hardware/lidar_driver')

    lidar_frame_id_arg = DeclareLaunchArgument(
        'lidar_frame_id', default_value='laser_frame',
        description='frame_id attached to LiDAR LaserScan messages')

    lidar_scan_topic_arg = DeclareLaunchArgument(
        'lidar_scan_topic', default_value='/scan',
        description='Topic published by the LiDAR driver')

    lidar_raw_packet_topic_arg = DeclareLaunchArgument(
        'lidar_raw_packet_topic', default_value='/lidar/raw_packet',
        description='Optional LiDAR raw packet topic for packet-level debugging')

    lidar_publish_raw_packets_arg = DeclareLaunchArgument(
        'lidar_publish_raw_packets', default_value='false',
        description='Publish raw LiDAR packets when packet-level debugging is needed')

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
        description='Base frame used by field sensor evidence TFs')

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

    no_motion_static_odom_tf_arg = DeclareLaunchArgument(
        'no_motion_static_odom_tf', default_value='false',
        description='Publish a no-motion odom -> base_link static TF for sensor-only evidence capture')

    no_motion_mock_odom_enabled_arg = DeclareLaunchArgument(
        'no_motion_mock_odom_enabled', default_value='false',
        description='Publish zero-speed synthetic /odom for no-motion route recorder software proof only')

    no_motion_mock_odom_topic_arg = DeclareLaunchArgument(
        'no_motion_mock_odom_topic', default_value='/odom',
        description='Topic used by the no-motion synthetic Odometry publisher')

    no_motion_mock_odom_rate_arg = DeclareLaunchArgument(
        'no_motion_mock_odom_rate', default_value='1.0',
        description='Publish rate for the no-motion synthetic Odometry publisher')

    no_motion_odom_frame_id_arg = DeclareLaunchArgument(
        'no_motion_odom_frame_id', default_value='odom',
        description='Parent odom frame used by no-motion evidence capture')

    slam_map_frame_arg = DeclareLaunchArgument(
        'slam_map_frame',
        default_value='map',
        description='SLAM map frame id used by slam_toolbox')

    slam_odom_frame_arg = DeclareLaunchArgument(
        'slam_odom_frame',
        default_value='odom',
        description='SLAM odom frame id used by slam_toolbox')

    slam_base_frame_arg = DeclareLaunchArgument(
        'slam_base_frame',
        default_value='base_link',
        description='SLAM base frame id used by slam_toolbox')

    map_dir_arg = DeclareLaunchArgument(
        'map_dir',
        default_value=PathJoinSubstitution([
            EnvironmentVariable('HOME'),
            '.ros',
            'trashbot_maps',
        ]),
        description='Directory where map_recorder writes learned map artifacts')

    default_map_name_arg = DeclareLaunchArgument(
        'default_map_name',
        default_value='trashbot_map',
        description='Base filename used by map_recorder for PGM/YAML map artifacts')

    use_sim_time = LaunchConfiguration('use_sim_time')
    record_interval = LaunchConfiguration('record_interval')
    pose_topic = LaunchConfiguration('pose_topic')
    route_recorder = LaunchConfiguration('route_recorder')
    waypoint_manager = LaunchConfiguration('waypoint_manager')
    route_output_dir = LaunchConfiguration('route_output_dir')
    route_camera_topic = LaunchConfiguration('route_camera_topic')
    route_odom_topic = LaunchConfiguration('route_odom_topic')
    route_min_distance_m = LaunchConfiguration('route_min_distance_m')
    route_frame_id = LaunchConfiguration('route_frame_id')
    route_id = LaunchConfiguration('route_id')
    route_sample_manifest_name = LaunchConfiguration('route_sample_manifest_name')
    route_sample_manifest_max_entries = LaunchConfiguration('route_sample_manifest_max_entries')
    camera_enabled = LaunchConfiguration('camera_enabled')
    camera_device = LaunchConfiguration('camera_device')
    camera_topic = LaunchConfiguration('camera_topic')
    camera_frame_id = LaunchConfiguration('camera_frame_id')
    camera_width = LaunchConfiguration('camera_width')
    camera_height = LaunchConfiguration('camera_height')
    camera_fps = LaunchConfiguration('camera_fps')
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
    no_motion_static_odom_tf = LaunchConfiguration('no_motion_static_odom_tf')
    no_motion_mock_odom_enabled = LaunchConfiguration('no_motion_mock_odom_enabled')
    no_motion_mock_odom_topic = LaunchConfiguration('no_motion_mock_odom_topic')
    no_motion_mock_odom_rate = LaunchConfiguration('no_motion_mock_odom_rate')
    no_motion_odom_frame_id = LaunchConfiguration('no_motion_odom_frame_id')
    slam_map_frame = LaunchConfiguration('slam_map_frame')
    slam_odom_frame = LaunchConfiguration('slam_odom_frame')
    slam_base_frame = LaunchConfiguration('slam_base_frame')
    map_dir = LaunchConfiguration('map_dir')
    default_map_name = LaunchConfiguration('default_map_name')
    no_motion_mock_odom_command = [
        'python3',
        '-c',
        (
            'import sys\n'
            'import rclpy\n'
            'from nav_msgs.msg import Odometry\n'
            'from rclpy.node import Node\n'
            'rate=float(sys.argv[1])\n'
            'topic=sys.argv[2]\n'
            'odom_frame=sys.argv[3]\n'
            'base_frame=sys.argv[4]\n'
            'rclpy.init()\n'
            'node=Node("no_motion_mock_odom_pub")\n'
            'publisher=node.create_publisher(Odometry, topic, 10)\n'
            'timer_period=1.0 / rate if rate > 0.0 else 1.0\n'
            'message=Odometry()\n'
            'message.header.frame_id=odom_frame\n'
            'message.child_frame_id=base_frame\n'
            'message.pose.pose.orientation.w=1.0\n'
            'def tick():\n'
            '    message.header.stamp=node.get_clock().now().to_msg()\n'
            '    publisher.publish(message)\n'
            'node.create_timer(timer_period, tick)\n'
            'tick()\n'
            'rclpy.spin(node)\n'
        ),
        no_motion_mock_odom_rate,
        no_motion_mock_odom_topic,
        no_motion_odom_frame_id,
        base_frame_id,
    ]

    return LaunchDescription([
        use_sim_time_arg,
        record_interval_arg,
        pose_topic_arg,
        route_recorder_arg,
        waypoint_manager_arg,
        route_output_dir_arg,
        route_camera_topic_arg,
        route_odom_topic_arg,
        route_min_distance_m_arg,
        route_frame_id_arg,
        route_id_arg,
        route_sample_manifest_name_arg,
        route_sample_manifest_max_entries_arg,
        camera_enabled_arg,
        camera_device_arg,
        camera_topic_arg,
        camera_frame_id_arg,
        camera_width_arg,
        camera_height_arg,
        camera_fps_arg,
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
        no_motion_static_odom_tf_arg,
        no_motion_mock_odom_enabled_arg,
        no_motion_mock_odom_topic_arg,
        no_motion_mock_odom_rate_arg,
        no_motion_odom_frame_id_arg,
        slam_map_frame_arg,
        slam_odom_frame_arg,
        slam_base_frame_arg,
        map_dir_arg,
        default_map_name_arg,

        # SLAM Toolbox 是 learn 入口的建图 source；no-motion 现场采集会用它验证 map_recorder 是否真的收到 /map。
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'mode': 'mapping',
                'map_frame': slam_map_frame,
                'odom_frame': slam_odom_frame,
                'base_frame': slam_base_frame,
                'scan_topic': lidar_scan_topic,
            }],
        ),

        # Map recorder 只负责保存已有地图数据，不能单独证明 SLAM 已经产出 /map。
        Node(
            package='ros2_trashbot_nav',
            executable='map_recorder',
            name='map_recorder',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                # map proof helper 显式传 runtime/maps，防止 artifact 分散到默认 HOME。
                'map_dir': map_dir,
                'default_map_name': default_map_name,
            }],
        ),

        # Waypoint manager 保持原学习模式行为，不依赖新增 sensor-only 参数。
        Node(
            package='ros2_trashbot_nav',
            executable='waypoint_manager',
            name='waypoint_manager',
            output='screen',
            condition=IfCondition(waypoint_manager),
            parameters=[{
                'use_sim_time': use_sim_time,
                'learn_mode': True,
                'record_interval': record_interval,
                'pose_topic': pose_topic,
            }],
        ),

        # 真实相机只在显式启用时拉起；默认指向现场已验证的 UVC capture，避免误绑 Cedrus decoder。
        Node(
            package='ros2_trashbot_vision',
            executable='camera_publisher',
            name='camera_publisher',
            output='screen',
            condition=IfCondition(camera_enabled),
            parameters=[{
                'device': camera_device,
                'topic': camera_topic,
                'frame_id': camera_frame_id,
                'width': camera_width,
                'height': camera_height,
                'fps': camera_fps,
            }],
        ),

        # LiDAR 默认关闭，现场显式传入 /dev/ttyACM0 @ 150000 时才打开，避免把无设备开发机误判成回归。
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
                'range_min': lidar_range_min,
                'range_max': lidar_range_max,
                'scan_time': lidar_scan_time,
                'time_increment': lidar_time_increment,
                'mock_packets': lidar_mock_packets,
                'mock_scan': lidar_mock_scan,
            }],
        ),

        # 该 TF 只用于 sensor stack 拓扑 smoke，不代表 laser_frame 已完成机械安装标定。
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

        # no-motion odom TF 只为 route/keyframe 软件链路补拓扑，不能当成真实里程计或 HIL 证据。
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='no_motion_static_odom_tf',
            output='screen',
            condition=IfCondition(no_motion_static_odom_tf),
            arguments=[
                '0.0',
                '0.0',
                '0.0',
                '0.0',
                '0.0',
                '0.0',
                no_motion_odom_frame_id,
                base_frame_id,
            ],
        ),

        # 使用 ROS2 CLI 发布零速 Odometry，避免新增包入口；该进程不发布 /cmd_vel，也不触碰底盘安全 gate。
        ExecuteProcess(
            cmd=no_motion_mock_odom_command,
            output='screen',
            condition=IfCondition(no_motion_mock_odom_enabled),
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
                'route_id': route_id,
                'sample_manifest_name': route_sample_manifest_name,
                'sample_manifest_max_entries': route_sample_manifest_max_entries,
            }],
        ),
    ])
