"""启动 Trashbot 远程只读 Foxglove 观察桥。"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # 远程观察要能被 PC 和同网段浏览器访问，所以默认监听所有网卡。
    address_arg = DeclareLaunchArgument(
        "address",
        default_value="0.0.0.0",
        description="WebSocket bind address for browser observation",
    )
    # 8765 是 PC summary 和 Foxglove Web 说明中固定暴露的地址，避免现场脚本猜端口。
    port_arg = DeclareLaunchArgument(
        "port",
        default_value="8765",
        description="WebSocket port for Foxglove Studio",
    )
    # 保留仿真时钟开关，便于同一观察配置复用于 mock、仿真和真实机器人。
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation clock when the observed ROS graph uses /clock",
    )
    # 远程排障需要知道 bridge 是否仍在线，因此 sysinfo 默认打开但仍只属于观察面。
    sysinfo_arg = DeclareLaunchArgument(
        "sysinfo",
        default_value="true",
        description="Publish bridge system information for remote diagnostics",
    )

    # LaunchConfiguration 保持命令行可覆盖，但默认值必须和 PC summary 中的合同一致。
    address = LaunchConfiguration("address")
    port = LaunchConfiguration("port")
    use_sim_time = LaunchConfiguration("use_sim_time")
    sysinfo = LaunchConfiguration("sysinfo")

    # 只开放观察面需要的 topic；不把底盘速度或业务控制 topic 暴露成远程控制入口。
    observe_topic_whitelist = [
        # 地图、雷达、TF、路线和定位是回答“地图太小/远程怎么看”的最小观察集合。
        "^/(map|map_metadata|scan|tf|tf_static|odom|plan|local_plan|amcl_pose|pose)$",
        # costmap 只用于工程判断 Nav2 周边状态，不允许在这里下发目标或服务调用。
        "^/(global_costmap|local_costmap)/(costmap|costmap_updates)$",
        # 相机图像只作为远程看画面补充；PC 共享预览仍是普通用户默认入口。
        "^/camera/(image_raw|camera_info)$",
        # sysinfo 只证明 bridge 在线，不能作为运动或建图完成证据。
        "^/foxglove_bridge/sysinfo$",
    ]

    # 这里直接启动 bridge 节点，避免嵌套调用 ros2 launch 时丢失本文件的白名单边界。
    return LaunchDescription(
        [
            address_arg,
            port_arg,
            use_sim_time_arg,
            sysinfo_arg,
            Node(
                package="foxglove_bridge",
                executable="foxglove_bridge",
                name="trashbot_foxglove_bridge",
                output="screen",
                parameters=[
                    {
                        # address/port 是远程观察入口；PC 页面不会自动启动这个节点。
                        "address": address,
                        "port": ParameterValue(port, value_type=int),
                        "use_sim_time": ParameterValue(use_sim_time, value_type=bool),
                        "sysinfo": ParameterValue(sysinfo, value_type=bool),
                        "topic_whitelist": observe_topic_whitelist,
                        # 禁止浏览器通过 bridge 发布 topic，真实运动仍必须走 PC 安全确认链路。
                        "client_topic_whitelist": ["(?!)"],
                        # 禁止远程调用 ROS services，避免绕过上车 API 的 fail-closed 代理。
                        "service_whitelist": ["(?!)"],
                        # 禁止远程改参数，避免观察页改变 Nav2、底盘或传感器 runtime。
                        "param_whitelist": ["(?!)"],
                        # 只保留连接图、静态资源和时间能力；不开放发布、服务或参数能力。
                        "capabilities": ["connectionGraph", "assets", "time"],
                    }
                ],
            ),
        ]
    )
