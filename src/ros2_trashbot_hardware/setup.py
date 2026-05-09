from setuptools import setup

package_name = 'ros2_trashbot_hardware'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyserial'],
    tests_require=['pytest'],
    zip_safe=True,
    maintainer='trashbot',
    maintainer_email='trashbot@local',
    description='Waveshare WAVE ROVER UART JSON bridge for trashbot',
    license='MIT',
    entry_points={
        'console_scripts': [
            'esp32_bridge = ros2_trashbot_hardware.esp32_bridge:main',
        ],
    },
)
