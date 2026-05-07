"""
ESP32 Serial Bridge - Orange Pi upper computer <-> ESP32 lower controller
Translates binary serial protocol to/from ROS2 topics.

Serial protocol (matches ESP32 firmware):
  ESP32 -> Pi: [0xAA 0x55] [seq] [type] [len] [payload] [checksum]
  Pi -> ESP32: [0xAA 0x55] [seq] [cmd] [len] [payload] [checksum]
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Range, Imu, BatteryState
from std_srvs.srv import Trigger
import serial
import struct
import threading
import time


# Protocol constants
HEADER1 = 0xAA
HEADER2 = 0x55

# Types: ESP32 -> Pi
TYPE_ODOM = 0x01
TYPE_ULTRASONIC = 0x02
TYPE_IMU = 0x03
TYPE_STATUS = 0x04

# Commands: Pi -> ESP32
CMD_STOP = 0x01
CMD_DRIVE = 0x02
CMD_SET_SPEED = 0x03
CMD_BEEP = 0x04
CMD_GET_STATUS = 0x05
CMD_RESET_ODOM = 0x06


class ESP32Bridge(Node):
    """Bidirectional bridge between ESP32 serial and ROS2 topics."""

    def __init__(self):
        super().__init__('esp32_bridge')

        # Serial configuration
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)

        port = self.get_parameter('port').value
        baudrate = self.get_parameter('baudrate').value

        # Parse state machine
        self._parse_state = 'header1'
        self._buf = bytearray()
        self._seq_in = 0

        # Connect to ESP32
        try:
            self.serial = serial.Serial(port, baudrate, timeout=0.01)
            self.get_logger().info(f'Connected to ESP32 on {port} @ {baudrate}')
        except serial.SerialException as e:
            self.get_logger().fatal(f'Cannot open serial port {port}: {e}')
            raise

        # Publishers
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)
        self.us_front_pub = self.create_publisher(Range, '/ultrasonic/front', 10)
        self.us_left_pub = self.create_publisher(Range, '/ultrasonic/left', 10)
        self.us_right_pub = self.create_publisher(Range, '/ultrasonic/right', 10)
        self.battery_pub = self.create_publisher(BatteryState, '/battery', 10)

        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self._cmd_vel_callback, 10)

        # Services
        self.stop_srv = self.create_service(
            Trigger, '/trashbot/stop', self._stop_callback)
        self.reset_odom_srv = self.create_service(
            Trigger, '/trashbot/reset_odom', self._reset_odom_callback)
        self.beep_srv = self.create_service(
            Trigger, '/trashbot/beep', self._beep_callback)

        # State
        self._seq_out = 0
        self._last_cmd_time = time.time()
        self._running = True
        self._serial_lock = threading.Lock()

        # Start reader thread
        self._reader_thread = threading.Thread(target=self._serial_reader, daemon=True)
        self._reader_thread.start()

        # Watchdog timer
        self.watchdog_timer = self.create_timer(0.5, self._watchdog_check)

        self.get_logger().info('ESP32Bridge ready. Publishing odometry, ultrasonic, IMU.')

    def _serial_reader(self):
        """Read bytes from serial in background thread."""
        while self._running:
            try:
                data = self.serial.read(1)
                if not data:
                    continue
                self._parse_byte(data[0])
            except Exception as e:
                self.get_logger().error(f'Serial read error: {e}')
                time.sleep(0.1)

    def _parse_byte(self, byte_val):
        """State machine for packet parsing."""
        if self._parse_state == 'header1':
            if byte_val == HEADER1:
                self._buf = bytearray([byte_val])
                self._parse_state = 'header2'
        elif self._parse_state == 'header2':
            if byte_val == HEADER2:
                self._buf.append(byte_val)
                self._parse_state = 'seq'
            else:
                self._parse_state = 'header1'
        elif self._parse_state == 'seq':
            self._buf.append(byte_val)
            self._parse_state = 'type'
        elif self._parse_state == 'type':
            self._buf.append(byte_val)
            self._parse_state = 'len'
        elif self._parse_state == 'len':
            self._buf.append(byte_val)
            self._payload_len = byte_val
            self._payload_received = 0
            self._parse_state = 'payload'
        elif self._parse_state == 'payload':
            self._buf.append(byte_val)
            self._payload_received += 1
            if self._payload_received >= self._payload_len:
                self._parse_state = 'checksum'
        elif self._parse_state == 'checksum':
            self._buf.append(byte_val)
            self._process_packet()
            self._parse_state = 'header1'

    def _process_packet(self):
        """Validate and process a complete packet."""
        if len(self._buf) < 5 + self._payload_len:
            return

        # Extract fields
        seq = self._buf[2]
        msg_type = self._buf[3]
        payload_len = self._buf[4]
        payload = self._buf[5:5 + payload_len]
        checksum = self._buf[5 + payload_len]

        # Verify checksum
        calc = seq ^ msg_type ^ payload_len
        for b in payload:
            calc ^= b
        if calc != checksum:
            self.get_logger().warn(f'Checksum mismatch: got {checksum}, calc {calc}')
            return

        self._seq_in = seq

        # Dispatch by type
        if msg_type == TYPE_ODOM:
            self._handle_odom(payload)
        elif msg_type == TYPE_ULTRASONIC:
            self._handle_ultrasonic(payload)
        elif msg_type == TYPE_IMU:
            self._handle_imu(payload)
        elif msg_type == TYPE_STATUS:
            self._handle_status(payload)

    def _handle_odom(self, payload):
        """Parse odometry data from ESP32."""
        if len(payload) < 20:
            return

        x = struct.unpack('<f', payload[0:4])[0]
        y = struct.unpack('<f', payload[4:8])[0]
        theta = struct.unpack('<f', payload[8:12])[0]
        enc_l = struct.unpack('<i', payload[12:16])[0]
        enc_r = struct.unpack('<i', payload[16:20])[0]

        now = self.get_clock().now().to_msg()

        msg = Odometry()
        msg.header.stamp = now
        msg.header.frame_id = 'odom'
        msg.child_frame_id = 'base_link'
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.position.z = 0.0

        # Simple quaternion from theta
        import math
        qz = math.sin(theta / 2.0)
        qw = math.cos(theta / 2.0)
        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw

        msg.twist.twist.linear.x = 0.0  # TODO: derive from encoder delta
        msg.twist.twist.angular.z = 0.0

        self.odom_pub.publish(msg)

    def _handle_ultrasonic(self, payload):
        """Parse ultrasonic distances."""
        if len(payload) < 12:
            return

        front = struct.unpack('<f', payload[0:4])[0]
        left = struct.unpack('<f', payload[4:8])[0]
        right = struct.unpack('<f', payload[8:12])[0]

        now = self.get_clock().now().to_msg()

        for pub, name, dist in [
            (self.us_front_pub, 'front', front),
            (self.us_left_pub, 'left', left),
            (self.us_right_pub, 'right', right),
        ]:
            msg = Range()
            msg.header.stamp = now
            msg.header.frame_id = f'ultrasonic_{name}'
            msg.radiation_type = Range.ULTRASOUND
            msg.field_of_view = 0.3
            msg.min_range = 0.02
            msg.max_range = 4.0
            msg.range = dist
            pub.publish(msg)

    def _handle_imu(self, payload):
        """Parse IMU heading."""
        if len(payload) < 4:
            return

        heading = struct.unpack('<f', payload[0:4])[0]

        import math
        now = self.get_clock().now().to_msg()
        msg = Imu()
        msg.header.stamp = now
        msg.header.frame_id = 'imu_link'
        qz = math.sin(heading / 2.0)
        qw = math.cos(heading / 2.0)
        msg.orientation.z = qz
        msg.orientation.w = qw
        self.imu_pub.publish(msg)

    def _handle_status(self, payload):
        """Parse ESP32 status."""
        if len(payload) < 3:
            return

        state = payload[0]
        watchdog = payload[1]
        battery_pct = payload[2]

        now = self.get_clock().now().to_msg()
        msg = BatteryState()
        msg.header.stamp = now
        msg.voltage = battery_pct / 100.0 * 12.0  # assume 12V max
        msg.percentage = float(battery_pct) / 100.0
        msg.present = True
        self.battery_pub.publish(msg)

    def _send_command(self, cmd, payload=b'') -> bool:
        """Send command packet to ESP32."""
        seq = self._seq_out
        length = len(payload)
        if length > 255:
            self.get_logger().error(f'Command payload too large: {length} bytes')
            return False

        header = struct.pack('<BBBBB', HEADER1, HEADER2, seq, cmd, length)
        data = header + payload

        checksum = seq ^ cmd ^ length
        for b in payload:
            checksum ^= b

        try:
            with self._serial_lock:
                if not self.serial.is_open:
                    return False
                self.serial.write(data + bytes([checksum]))
        except serial.SerialException as exc:
            self.get_logger().error(f'Serial write error: {exc}')
            return False

        self._seq_out = (self._seq_out + 1) & 0xFF
        self._last_cmd_time = time.time()
        return True

    def _cmd_vel_callback(self, msg: Twist):
        """Convert /cmd_vel to ESP32 differential drive command."""
        linear = msg.linear.x    # m/s
        angular = msg.angular.z  # rad/s

        payload = struct.pack('<ff', linear, angular)
        if not self._send_command(CMD_SET_SPEED, payload):
            self.get_logger().warn('Failed to forward /cmd_vel to ESP32')

    def _stop_callback(self, request, response):
        response.success = self._send_command(CMD_STOP)
        response.message = 'Motors stopped' if response.success else 'Failed to send stop command'
        return response

    def _reset_odom_callback(self, request, response):
        response.success = self._send_command(CMD_RESET_ODOM)
        response.message = 'Odometry reset' if response.success else 'Failed to send reset odom command'
        return response

    def _beep_callback(self, request, response):
        response.success = self._send_command(CMD_BEEP)
        response.message = 'Beep sent' if response.success else 'Failed to send beep command'
        return response

    def _watchdog_check(self):
        """Check if ESP32 is still responding."""
        if time.time() - self._last_cmd_time > 2.0:
            self.get_logger().warn('No commands sent recently - ESP32 watchdog idle')

    def destroy_node(self):
        self._running = False
        self._send_command(CMD_STOP)
        if hasattr(self, 'serial') and self.serial.is_open:
            self.serial.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ESP32Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
