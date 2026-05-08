from setuptools import setup
import os
from glob import glob

package_name = 'ros2_trashbot_nav'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),
    ],
    install_requires=['setuptools'],
    tests_require=['pytest'],
    zip_safe=True,
    maintainer='trashbot',
    maintainer_email='trashbot@local',
    description='Navigation and waypoint management for trashbot',
    license='MIT',
    entry_points={
        'console_scripts': [
            'waypoint_manager = ros2_trashbot_nav.waypoint_manager:main',
            'nav_to_goal = ros2_trashbot_nav.nav_to_goal:main',
            'map_recorder = ros2_trashbot_nav.map_recorder:main',
            'fixed_route_autonomy = ros2_trashbot_nav.fixed_route_autonomy:main',
            'route_data_recorder = ros2_trashbot_nav.route_data_recorder:main',
            'route_csv_to_yaml = ros2_trashbot_nav.route_csv_to_yaml:main',
            'keyframe_camera_sim = ros2_trashbot_nav.keyframe_camera_sim:main',
            'route_debug_web = ros2_trashbot_nav.route_debug_web:main',
        ],
    },
)
