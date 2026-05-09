from setuptools import setup

package_name = 'ros2_trashbot_vision'

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
    description='Vision-based trash detection for trashbot',
    license='MIT',
    entry_points={
        'console_scripts': [
            'trash_detector = ros2_trashbot_vision.trash_detector:main',
        ],
    },
)
