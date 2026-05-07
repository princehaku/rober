import os

import rclpy
from rclpy.node import Node
from ros2_trashbot_nav.route_utils import load_waypoints_from_csv


class RouteCsvToYaml(Node):
    """Convert recorded route.csv to fixed_route.yaml format."""

    def __init__(self):
        super().__init__('route_csv_to_yaml')
        self.declare_parameter('input_csv', '~/.ros/trashbot_runs/run_001/route.csv')
        self.declare_parameter('output_yaml', '~/.ros/trashbot_maps/fixed_route.yaml')
        self.declare_parameter('frame_id', 'map')
        self.input_csv = os.path.expanduser(self.get_parameter('input_csv').value)
        self.output_yaml = os.path.expanduser(self.get_parameter('output_yaml').value)
        self.frame_id = self.get_parameter('frame_id').value

    def convert(self) -> bool:
        if not os.path.exists(self.input_csv):
            self.get_logger().error(f'CSV not found: {self.input_csv}')
            return False
        waypoints = load_waypoints_from_csv(self.input_csv, self.frame_id)
        import yaml
        output_dir = os.path.dirname(self.output_yaml)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(self.output_yaml, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'waypoints': waypoints}, f, sort_keys=False)
        self.get_logger().info(
            f'Converted {len(waypoints)} points: {self.input_csv} -> {self.output_yaml}')
        return True


def main(args=None):
    rclpy.init(args=args)
    node = RouteCsvToYaml()
    try:
        ok = node.convert()
        if not ok:
            raise SystemExit(1)
    finally:
        node.destroy_node()
        rclpy.shutdown()
