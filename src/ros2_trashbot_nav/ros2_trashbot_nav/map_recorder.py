import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, MapMetaData
from std_srvs.srv import Trigger
import yaml
import os


class MapRecorder(Node):
    """Saves and loads maps. Handles the learn-phase map persistence."""

    def __init__(self):
        super().__init__('map_recorder')

        self.declare_parameter('map_dir', '~/.ros/trashbot_maps')
        self.map_dir = os.path.expanduser(self.get_parameter('map_dir').value)
        os.makedirs(self.map_dir, exist_ok=True)

        self.declare_parameter('default_map_name', 'trashbot_map')
        self.default_map_name = self.get_parameter('default_map_name').value

        # Subscribe to map topic
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self._map_callback, 10)

        # Service to save map
        self.save_map_srv = self.create_service(
            Trigger, '/trashbot/save_map', self._save_map)

        self.latest_map = None
        self.latest_map_meta = None

    def _map_callback(self, msg: OccupancyGrid):
        self.latest_map = msg

    def _save_map(self, request, response):
        """Save current map to disk."""
        success, message = self.save_current_map()
        response.success = success
        response.message = message
        return response

    def save_current_map(self):
        """Save current map to disk and return a service-compatible result."""
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
        """Write occupancy grid to PGM image."""
        width = msg.info.width
        height = msg.info.height
        data = msg.data

        with open(path, 'wb') as f:
            # PGM header
            f.write(f'P5\n# trashbot map {width}x{height}\n{width} {height}\n255\n'.encode())
            # Convert occupancy to grayscale: -1->205(free), 0->205, 100->0(wall)
            pixels = []
            for val in data:
                if val == -1:
                    pixels.append(205)  # unknown
                elif val == 0:
                    pixels.append(205)  # free
                else:
                    pixels.append(0)    # occupied
            f.write(bytes(pixels))

    def _write_yaml(self, msg: OccupancyGrid, path: str):
        """Write map metadata as YAML."""
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
