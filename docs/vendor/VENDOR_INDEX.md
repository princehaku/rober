# Vendor Hardware and Software Reference Index

This is the required entry point for hardware, wiring, firmware, and vendor
software references in this project.

Before changing robot hardware integration, serial communication, GPIO, motor
control, firmware assumptions, launch defaults, or ROS2 driver behavior, read
this file first and then open the referenced source documents. Do not guess pin
definitions, protocol fields, baud rates, command IDs, voltage levels, or
mechanical dimensions from memory.

## Source Of Truth Order

1. Local vendor files under `docs/vendor/`.
2. Vendor source code and firmware comments in this index.
3. Project ROS2 code under `src/`.
4. Online documents only when a local file is missing or visibly outdated.

When local vendor references conflict with existing ROS2 code, treat that as an
integration issue and resolve it explicitly in code or documentation.

## Hardware Stack

- Main SBC: Orange Pi Zero 3, H618.
- Mobile base: Waveshare WAVE ROVER.
- Lower controller: ESP32 firmware from Waveshare WAVE ROVER package.
- Upper/lower controller link: UART, newline-delimited JSON.
- Project role: ROS2 Humble autonomous trash collection robot.

## Orange Pi Zero 3

Directory: `docs/vendor/orangepizero3/`

### Files

- `OrangePi_Zero3_H618_用户手册_v1.6.pdf`
  - Main SBC user manual.
  - Use for OS image flashing, boot media, SSH, network, serial, GPIO, 26-pin
    header, 13-pin header, USB, and Linux setup.
  - The table of contents includes 26-pin/13-pin sections around manual pages
    37-38. Check the PDF before wiring.
- `OrangePi-ZERO3_电路图.pdf`
  - Board schematic.
  - Use for GPIO voltage domains, pin mux, power rails, UART/I2C/SPI signals,
    USB, LEDs, and board-level electrical checks.
  - The schematic explicitly warns that external IO voltage must match the SOC
    GPIO voltage and pull-up voltage domain.

### Agent Rules

- For Orange Pi pinout or voltage work, open both the user manual and schematic.
- Do not assume Raspberry Pi pin numbering applies to Orange Pi.
- Confirm the actual Linux serial device name on target hardware before
  hardcoding it. The WAVE ROVER sample uses Raspberry Pi paths, not Orange Pi
  paths.

## Waveshare WAVE ROVER

Directory: `docs/vendor/waveshare_wave_rover/`

### Main Documents And Mechanical Files

- `WAVE_ROVER.wiki.html`
  - Saved WAVE ROVER wiki page.
- `wiki_assets/`
  - Images referenced by the saved wiki page.
- `WAVE ROVER PDF.pdf`
  - Chassis/mechanical PDF reference.
- `WAVE ROVER DXF.dxf`
  - Chassis DXF drawing.
- `WAVE ROVER-EP PDF.pdf`
  - Extension platform PDF reference.
- `WAVE ROVER-EP DXF.dxf`
  - Extension platform DXF drawing.
- `WAVE ROVER_MODEL_STL.stl`
  - 3D model.

Use the PDF/DXF/STL files for mounting, bracket design, sensor placement, and
clearance checks. Do not infer dimensions from photos.

### ESP32 Lower Controller Firmware

Canonical extracted source:

- `WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`
- `WAVE_ROVER_V0.9/json_cmd.h`
- `WAVE_ROVER_V0.9/uart_ctrl.h`
- `WAVE_ROVER_V0.9/movtion_module.h`
- `WAVE_ROVER_V0.9/IMU_ctrl.h`
- `WAVE_ROVER_V0.9/battery_ctrl.h`
- `WAVE_ROVER_V0.9/gimbal_module.h`
- `WAVE_ROVER_V0.9/oled_ctrl.h`
- `WAVE_ROVER_V0.9/ugv_config.h`
- `WAVE_ROVER_V0.9/data/devConfig.json`
- `WAVE_ROVER_V0.9/data/wifiConfig.json`

There is also a duplicate nested extraction at
`WAVE_ROVER/WAVE_ROVER_V0.9/`. Prefer the top-level `WAVE_ROVER_V0.9/` path for
new references unless comparing archives.

### Factory Firmware

- `WAVE_ROVER_FACTORY/flash_download_tool_3.9.5/flash_download_tool_3.9.5.exe`
  - ESP flash download tool.
- `WAVE_ROVER_FACTORY/flash_download_tool_3.9.5/bin/`
  - Factory binary components.
- `WAVE_ROVER_FACTORY/flash_download_tool_3.9.5/combine/target.bin`
  - Combined factory firmware image.
- `WAVE_ROVER_FACTORY/flash_download_tool_3.9.5/doc/Flash_Download_Tool__cn.pdf`
- `WAVE_ROVER_FACTORY/flash_download_tool_3.9.5/doc/Flash_Download_Tool__en.pdf`

Do not modify or overwrite factory binaries unless explicitly asked.

### Raspberry Pi Upper Computer Reference

Directory: `waveshare_wave_rover/ugv_rpi/`

Important files:

- `README.md`
  - Vendor app overview and install notes.
- `base_ctrl.py`
  - Primary Python reference for UART JSON communication with the ESP32.
- `config.yaml`
  - Vendor application command IDs, feedback keys, speed limits, video settings,
    and base options.
- `app.py`
  - Web app and high-level application wiring.
- `cv_ctrl.py`
  - Vendor computer vision behavior reference.
- `setup.sh`, `autorun.sh`, `99-dai.rules`
  - Linux install, autostart, and device rule references.
- `tutorial_cn/02 Python 底盘运动控制.ipynb`
- `tutorial_cn/06 获取底盘反馈信息.ipynb`
- `tutorial_cn/07 使用 JSON 指令控制下位机.ipynb`
- `tutorial_cn/08 下位机 JSON 指令集.ipynb`
- `tutorial_cn/21 基于 OpenCV 的巡线自动驾驶.ipynb`
- `tutorial_cn/25 主程序架构介绍.ipynb`
- `tutorial_cn/26 YAML 配置文件设置.ipynb`

The English tutorial directory mirrors the Chinese tutorial directory:
`ugv_rpi/tutorial_en/`.

### UART And JSON Control Facts

These facts come from `ugv_rpi/base_ctrl.py`,
`ugv_rpi/config.yaml`, and `WAVE_ROVER_V0.9/json_cmd.h`.

- Transport: serial UART.
- Framing: one JSON object per line, encoded as UTF-8, ending with `\n`.
- Vendor Raspberry Pi default: `/dev/ttyAMA0` at `115200`.
- Vendor Raspberry Pi alternate comment: `/dev/serial0` at `115200`.
- The ROS2 Orange Pi target may expose a different UART device. Confirm on the
  robot before setting launch defaults.

Key chassis commands:

- `{"T":1,"L":0.5,"R":0.5}`
  - `CMD_SPEED_CTRL`.
  - Left/right speed command used by `base_ctrl.py`.
- `{"T":11,"L":164,"R":164}`
  - `CMD_PWM_INPUT`.
  - Direct PWM input, signed range noted by firmware comment.
- `{"T":13,"X":0.1,"Z":0.3}`
  - `CMD_ROS_CTRL`.
  - Linear/angular velocity command in m/s and rad/s according to firmware
    comment. Prefer this for ROS `cmd_vel` mapping if hardware testing confirms
    it behaves correctly on this chassis.
- `{"T":130}`
  - `CMD_BASE_FEEDBACK`.
  - Request base feedback.
- `{"T":131,"cmd":1}` / `{"T":131,"cmd":0}`
  - `CMD_BASE_FEEDBACK_FLOW`.
  - Enable or disable streaming feedback.
- `{"T":142,"cmd":0}`
  - `CMD_FEEDBACK_FLOW_INTERVAL`.
  - Feedback interval command.
- `{"T":143,"cmd":0}`
  - `CMD_UART_ECHO_MODE`.
  - UART echo mode command.

Other useful command groups:

- OLED: `T=3`, default `T=-3`.
- IMU: `T=126`, `T=127`, `T=128`, `T=129`.
- LED: `T=132`.
- Gimbal: `T=133`, `T=134`, `T=135`, `T=137`, `T=141`.
- Speed rate: `T=138`, `T=139`, `T=140`.
- Arm/servo commands: `T=100` through `T=125`, plus related servo commands in
  `json_cmd.h`.
- File/mission commands: `T=200` and above in `json_cmd.h`.

### Integration Rules For ROS2 Work

- Before implementing a base driver, inspect:
  - `waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - `waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- Map ROS `geometry_msgs/Twist` to `T=13` only after verifying on hardware.
  If `T=13` is not supported by the loaded firmware, fall back to `T=1` with an
  explicit differential-drive conversion documented in code.
- Keep serial device, baud rate, max speed, and command mode configurable in
  launch parameters.
- Do not hardcode Raspberry Pi UART paths for Orange Pi.
- Do not use WiFi credentials from vendor example JSON files as project
  defaults.
- Any wiring or power decision must cite the Orange Pi schematic/manual and the
  WAVE ROVER mechanical/electrical references.

## LiDAR References: ROS2 Current And ROS1 Historical

Current ROS2/STC reference directory: `docs/vendor/lidar_pkg_ros2-main/`

Historical ROS1/protocol reference directory: `docs/vendor/lidar_ros/`

Use `lidar_pkg_ros2-main` for the current robot LiDAR implementation and
manual-start evidence. Keep `lidar_ros` as a historical ROS1/protocol snapshot
only; it remains useful for comparing the older `0xAA 0x55` packet parser,
`150000` baud reference, and raw packet topic shape, but it is not the current
ROS2 driver source of truth.

### Files

Current ROS2/STC files:

- `README.md`
  - ROS2 Humble usage notes for the current STC USB Serial LiDAR reference.
- `src/lidar_node.cpp`
  - ROS2 C++ reference driver/parser. Opens the serial device at `150000`,
    sends `A5 60` to start the LiDAR motor, syncs packets on `0xAA 0x55`, and
    publishes `sensor_msgs/msg/LaserScan`.
- `config/lidar_params.yaml`
  - Default ROS2 parameters. Current vendor reference uses `port_name:
    "/dev/lidar"` and `frame_id: "laser"`.
- `scripts/99-lidar.rules`
  - udev mapping for STC USB Serial: `idVendor=34bf`, `idProduct=ff0a`,
    symlink `lidar`.
- `launch/lidar.launch.py`
  - Headless LiDAR node launch reference.
- `launch/monitor.launch.py`
  - LiDAR node plus RViz/static robot description launch reference.
- `rviz/lidar.rviz`
  - RViz display reference; scan topic is `/scan`.
- `urdf/lidar.urdf`
  - Minimal LiDAR URDF reference.
- `models/lidar_mount.stl`
  - LiDAR mount model reference.

Historical ROS1/protocol files:

- `lidar_ros/SOURCE.md`
  - Snapshot provenance for `https://github.com/sudreamcarver/lidar_ros` at
    commit `a88fcec0a207e0a2765fb4542ffbc8b1913f60ee`, retrieved
    `2026-06-01T01:46:25Z`.
- `lidar_ros/README.md`
  - Historical description of the拆机 YDLIDAR test program, packet structure,
    parsing formulas, and ROS1 topic architecture.
- `lidar_ros/plot.py`
  - Historical standalone Python serial plotting reference using `/dev/ttyUSB0`
    at `150000` baud and `0xAA 0x55` packet synchronization.
- `lidar_ros/src/lidar_pkg/scripts/lidar_driver.py`
  - Historical ROS1 raw serial reader publishing `/lidar/raw_packet`
    (`std_msgs/UInt8MultiArray`) after syncing on `0xAA 0x55`.
- `lidar_ros/src/lidar_pkg/src/lidar_driver.cpp`
  - Historical ROS1 packet parser publishing `sensor_msgs/LaserScan` on the
    private `scan` topic under node namespace.
- `lidar_ros/src/lidar_pkg/rviz/lidar_config.rviz`
  - Historical RViz reference: fixed frame `laser_frame`, displayed topic
    `/lidar_parser_node/scan`.

### Verified Reference Facts

- This local reference is ROS2 Humble / ament CMake.
- The LiDAR USB bridge enumerates as STC USB Serial with `idVendor=34bf` and
  `idProduct=ff0a`; the vendor udev rule maps it to `/dev/lidar`.
- User manual test on 2026-06-02 confirmed `/dev/ttyACM0` at `150000` baud
  starts the motor after writing `A5 60`.
- The ROS2 C++ reference sends `A5 60` on startup.
- The ROS2 C++ reference sends `A5 00 A5 65 A5 65` during shutdown.
- The default ROS2 config uses `port_name: "/dev/lidar"`.
- Packet sync header is `0xAA 0x55`; packet length is derived from `LSN`.
- The parser publishes `sensor_msgs/msg/LaserScan` on `scan`; RViz references
  `/scan`.
- The default vendor frame id is `laser`; the project launch may override this
  to `laser_frame` when paired with `base_link -> laser_frame` TF.
- The historical `docs/vendor/lidar_ros/` snapshot is ROS1/catkin, not
  ROS2/ament. It shares `150000` baud and `0xAA 0x55` packet sync references,
  but its `/dev/ttyUSB0`, ROS1 launch, and namespaced scan topic are not current
  robot defaults.

### Agent Rules

- Use `docs/vendor/lidar_pkg_ros2-main/` as the LiDAR source of truth.
- Do not treat `docs/vendor/lidar_ros/` as removed or as the current robot
  source of truth. It is retained only as historical ROS1/protocol reference.
- Keep LiDAR serial port, baud rate, `frame_id`, raw topic, scan topic,
  startup command, shutdown command, and range/scan timing parameters
  configurable in ROS2 launch/config.
- Confirm the robot's real LiDAR USB path on target hardware before using a
  default. Current observed candidate is `/dev/ttyACM0`; stable deployment
  should prefer `/dev/lidar` or `/dev/serial/by-id/...` after udev validation.
- Treat `150000` baud, `A5 60`, `A5 00 A5 65 A5 65`, `0xAA 0x55`, `/scan`, and
  `/lidar/raw_packet` as software/reference plus manual-start evidence until a
  real ROS2 run records `source=hil_pass`.

## Complete Material Coverage

The local vendor tree currently covers:

- Orange Pi Zero 3 user manual and schematic.
- WAVE ROVER saved wiki page and wiki images.
- WAVE ROVER mechanical PDF, DXF, extension platform PDF/DXF, and STL model.
- WAVE ROVER ESP32 Arduino source, headers, build artifacts, and config JSON.
- WAVE ROVER factory flash tool, binary images, and flashing documentation.
- Waveshare Raspberry Pi upper-computer app, tutorials, web UI, CV models,
  install scripts, media, and configuration.
- LiDAR ROS2 reference snapshot `lidar_pkg_ros2-main`, including STC udev rule,
  startup/shutdown bytes, packet parsing, ROS2 launch/config, RViz, URDF, and
  mount model.
- LiDAR historical ROS1/protocol snapshot `lidar_ros`, retained for comparison
  with older parser/topic behavior and not used as the current ROS2 source of
  truth.

For generated UI assets, placeholder media, fonts, audio clips, and duplicated
build artifacts, use them only as vendor app reference. They are not project
architecture sources.

## ENTINA Tina2C Printing Reference

- [Tina2C printing source notes](entina_tina2c/PRINT_REFERENCE.md)
  - Official domestic/international links, checked 2026-11-01: 100×100×100 mm,
    0.4 mm nozzle, 1.75 mm PLA, no heated bed, slicer/TF workflow and boundaries.
  - This is a local printing-tool reference, with no change to robot hardware facts.

## JGA12-N20 Printed Drive Reference

- [N20 source notes and interfaces](n20_reference/REFERENCE.md)
  - 用户提供的商家工程图、尺寸图和配件图；用户确认 3 V、60 RPM。
  - 机械接口采用商品图，持续扭矩、带载速度及实际配合仍未验证。
  - 附 Fast-Rite 螺母尺寸基准；Pololu 仅作独立外形家族对照，不替代用户型号。
