"""启动 Trashbot 只读 RViz 观察视图。"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value=PathJoinSubstitution(
            [FindPackageShare("ros2_trashbot_bringup"), "rviz", "trashbot_nav.rviz"]
        ),
        description="RViz config that observes /map, /scan, /camera/image_raw, TF, Nav2 path and AMCL pose",
    )

    rviz_config = LaunchConfiguration("rviz_config")

    return LaunchDescription(
        [
            rviz_config_arg,
            Node(
                package="rviz2",
                executable="rviz2",
                name="trashbot_rviz",
                arguments=["-d", rviz_config],
                output="screen",
            ),
        ]
    )
