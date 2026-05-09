from setuptools import setup

package_name = 'ros2_trashbot_behavior'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    tests_require=['pytest'],
    zip_safe=True,
    maintainer='trashbot',
    maintainer_email='trashbot@local',
    description='Behavior coordination and task orchestration for trashbot',
    license='MIT',
    entry_points={
        'console_scripts': [
            'task_orchestrator = ros2_trashbot_behavior.task_orchestrator:main',
            'operator_gateway = ros2_trashbot_behavior.operator_gateway:main',
            'remote_bridge = ros2_trashbot_behavior.remote_bridge:main',
            'legacy_trash_collection_server = ros2_trashbot_behavior.trash_collection_server:main',
        ],
    },
)
