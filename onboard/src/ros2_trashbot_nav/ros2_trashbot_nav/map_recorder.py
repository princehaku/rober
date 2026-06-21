import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, MapMetaData
from std_srvs.srv import Trigger
import yaml
import os


class MapRecorder(Node):
    """保存学习阶段地图，供后续 Nav2 与路线复盘复用。"""

    def __init__(self):
        super().__init__('map_recorder')

        self.declare_parameter('map_dir', '~/.ros/trashbot_maps')
        self.map_dir = os.path.expanduser(self.get_parameter('map_dir').value)
        os.makedirs(self.map_dir, exist_ok=True)

        self.declare_parameter('default_map_name', 'trashbot_map')
        self.default_map_name = self.get_parameter('default_map_name').value

        # 地图保存只消费 SLAM 的 /map，不在这里启动或控制底盘。
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self._map_callback, 10)

        # 保存动作由显式服务触发，避免学习阶段每帧地图都写盘。
        self.save_map_srv = self.create_service(
            Trigger, '/trashbot/save_map', self._save_map)

        self.latest_map = None
        self.latest_map_meta = None

    def _map_callback(self, msg: OccupancyGrid):
        self.latest_map = msg

    def _save_map(self, request, response):
        """把最近一次 /map 写成 ROS map_server 可读的 YAML/PGM。"""
        success, message = self.save_current_map()
        response.success = success
        response.message = message
        return response

    def save_current_map(self):
        """保存当前地图，并返回 Trigger service 能直接使用的结果。"""
        if self.latest_map is None:
            return False, 'No map data received'

        map_path = os.path.join(self.map_dir, f'{self.default_map_name}.pgm')
        yaml_path = os.path.join(self.map_dir, f'{self.default_map_name}.yaml')

        try:
            self._write_pgm(self.latest_map, map_path)
            self._write_yaml(self.latest_map, yaml_path)
            message = f'Map saved to {map_path}'
            self.get_logger().info(message)
            return True, message
        except Exception as e:
            message = f'Failed to save map: {e}'
            self.get_logger().error(message)
            return False, message

    def _write_pgm(self, msg: OccupancyGrid, path: str):
        """把 OccupancyGrid 写成 map_server 约定的 PGM 灰度图。"""
        width = msg.info.width
        height = msg.info.height
        data = msg.data

        with open(path, 'wb') as f:
            # PGM header 保留注释，便于现场 artifact 直接识别尺寸来源。
            f.write(f'P5\n# trashbot map {width}x{height}\n{width} {height}\n255\n'.encode())
            # ROS map_server 约定：unknown=205，free=254，occupied=0；free 不能写成 unknown。
            pixels = []
            for val in data:
                if val == -1:
                    pixels.append(205)  # unknown
                elif val == 0:
                    pixels.append(254)  # free
                else:
                    pixels.append(0)    # occupied
            f.write(bytes(pixels))

    def _write_yaml(self, msg: OccupancyGrid, path: str):
        """写出 Nav2/map_server 可加载的地图元数据。"""
        data = {
            'image': os.path.basename(path).replace('.yaml', '.pgm'),
            'resolution': msg.info.resolution,
            'origin': [msg.info.origin.position.x, msg.info.origin.position.y, 0.0],
            'negate': 0,
            'occupied_thresh': 0.65,
            'free_thresh': 0.196,
        }
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)


def main(args=None):
    rclpy.init(args=args)
    node = MapRecorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.save_current_map()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
