# Board Camera Default Field Harden Tech Done

- sprint_type: epic
- owner: robot-software-engineer
- time: 2026-06-10 03:22 Asia/Shanghai
- software_proof_only=false
- deployed_field_smoke_proven=true
- ros_camera_topic_proven=true
- visible_content_proven=false
- safe_to_control=false
- delivery_success=false
- motion_commands_sent=false
- default_camera_device_smoke_proven=true

## 实际改动

本轮按 PRD/tech-plan 的 FP1-FP4 完成默认设备固化和防回退验证：

- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
  - 将 `camera_device` launch argument 默认值从 `/dev/video0` 改为 `/dev/video1`。
- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
  - 将 `camera_device` launch argument 默认值从 `/dev/video0` 改为 `/dev/video1`。
  - 更新相机节点旁中文注释，说明默认指向现场已验证的 UVC capture，目的是避免误绑 Cedrus decoder。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 新增 `test_field_camera_default_uses_verified_capture_device`，静态检查 `bringup.launch.py` 和 `learn.launch.py` 默认 `/dev/video1`，且不再含 `/dev/video0` 默认值。
  - 同时检查相机仍受 `camera_enabled` 条件控制，且节点参数继续传递 `camera_device`。
- `docs/vision/board_camera_publisher.md`
  - 同步说明当前现场 `bringup.launch.py` 与 `learn.launch.py` 默认已固化为 `/dev/video1`。
  - 保留 `/dev/video0` 是 Cedrus decoder 的失败样例边界。
  - 明确 `visible_content_proven=false` 仍成立，不能把默认设备固化等同于可用视觉内容。
- `sprints/2026.06.10_03-10_board-camera-default-field-harden/tech-done.md`
  - 记录本轮实现、接口影响、验证结果、失败定位和剩余风险。

资料来源：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vision/board_camera_publisher.md`
- `sprints/2026.06.10_03-10_board-camera-default-field-harden/pre_start.md`
- `sprints/2026.06.10_03-10_board-camera-default-field-harden/prd.md`
- `sprints/2026.06.10_03-10_board-camera-default-field-harden/tech-plan.md`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/tech-done.md`

## 接口影响

- ROS topic 不变：相机默认仍发布 `/camera/image_raw`，消息类型仍为 `sensor_msgs/msg/Image`。
- Launch 参数名不变：`camera_device`、`camera_topic`、`camera_frame_id`、`camera_width`、`camera_height`、`camera_fps` 均保持兼容。
- 行为变化仅限相机启用后未显式传 `camera_device` 的场景：默认从 `/dev/video0` 改为 `/dev/video1`。
- `camera_enabled` 语义不变：默认仍为 `false`，不会因为设备默认值变化而自动启动相机。
- 安全边界不变：本轮不修改 `/cmd_vel`、底盘串口、WAVE ROVER、ESP32、UART、LiDAR、Nav2、任务编排、手机端或云端。

## 验证结果

### 1. 静态检索

命令：

```bash
rg "camera_device|/dev/video[01]|visible_content_proven|ros_camera_topic_proven" onboard/src/ros2_trashbot_bringup/launch docs/vision/board_camera_publisher.md onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py
```

关键输出：

```text
onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py:
  'camera_device', default_value='/dev/video1',
onboard/src/ros2_trashbot_bringup/launch/learn.launch.py:
  'camera_device', default_value='/dev/video1',
onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py:
  self.assertIn("'camera_device', default_value='/dev/video1'", source)
  self.assertNotIn("'camera_device', default_value='/dev/video0'", source)
docs/vision/board_camera_publisher.md:
  `bringup.launch.py` 与 `learn.launch.py` 现场默认 `/dev/video1`
  `visible_content_proven=false`
  `ros_camera_topic_proven=true`
```

结论：FP1、FP2、FP3、FP4 的静态契约均可检索到。

### 2. launch contract unittest

命令：

```bash
python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py
```

输出：

```text
................
----------------------------------------------------------------------
Ran 16 tests in 0.027s

OK
```

结论：静态 launch contract 测试通过，包含相机默认 `/dev/video1` 防回退检查。

### 3. Docker/Humble build

第一次运行命令：

```bash
bash onboard/scripts/docker_humble_build.sh
```

第一次失败定位：

```text
rm: cannot remove 'build/ros2_trashbot_interfaces': Directory not empty
```

根因：镜像构建成功，但容器内进入 `colcon build` 前清理旧 `build/ install/ log/` 生成目录时失败；不是本轮 launch/test/doc 编译错误。随后按脚本预期清理本地生成目录 `onboard/build onboard/install onboard/log` 后重跑同一 Docker/Humble 验收。

重跑命令：

```bash
bash onboard/scripts/docker_humble_build.sh
```

关键输出：

```text
not found: "/ws/install/ros2_trashbot_vision/share/ros2_trashbot_vision/hook/ament_prefix_path.sh"
Starting >>> ros2_trashbot_interfaces
Starting >>> ros2_trashbot_vision
Finished <<< ros2_trashbot_vision [1.56s]
Finished <<< ros2_trashbot_interfaces [42.8s]
Starting >>> ros2_trashbot_nav
Starting >>> ros2_trashbot_hardware
Finished <<< ros2_trashbot_nav [2.12s]
Starting >>> ros2_trashbot_behavior
Finished <<< ros2_trashbot_hardware [2.17s]
Finished <<< ros2_trashbot_behavior [1.59s]
Starting >>> ros2_trashbot_bringup
Finished <<< ros2_trashbot_bringup [5.80s]

Summary: 6 packages finished [52.7s]
```

结论：Docker/Humble `colcon build --symlink-install` 通过。`not found ... ament_prefix_path.sh` 是清理旧 install 后 source 环境遗留警告，未影响最终构建。

### 4. 真实上位机部署和 no-motion camera smoke

真实上位机 SSH 可达：

```text
remote_ssh=ok
op-z3-b6.home
ros_setup=present
rober_install=present
/dev/video0
/dev/video1
/dev/video2
```

部署前只读检查远端当前源码默认值：

```text
/root/rober/onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py:117:
        'camera_device', default_value='/dev/video0',
/root/rober/onboard/src/ros2_trashbot_bringup/launch/learn.launch.py:74:
        'camera_device', default_value='/dev/video0',
```

部署前按要求在远端运行不显式传 `camera_device` 的 no-motion smoke：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  camera_enabled:=true \
  camera_width:=640 \
  camera_height:=480 \
  camera_fps:=2.0
```

关键输出：

```text
== topic info ==
Unknown topic '/camera/image_raw'
== topic metadata sample ==
image_message_observed=false
[camera_publisher-3] RuntimeError: Failed to open camera device /dev/video0; camera_publisher fails closed and will not fabricate frames
[ERROR] [camera_publisher-3]: process has died [pid 89712, exit code 1, cmd '/root/rober/onboard/install/ros2_trashbot_vision/lib/ros2_trashbot_vision/camera_publisher --ros-args -r __node:=camera_publisher --params-file /tmp/launch_params_4dqj10hi'].
== cleanup check ==
```

部署前失败定位：

- 真实上位机当前 `/root/rober/onboard/src` 和已安装 launch 仍是旧默认 `/dev/video0`，本轮本地改动尚未部署到远端。
- smoke 因远端旧默认误绑 Cedrus decoder 失败，正好复现本 sprint 要消除的现场风险。
- 清理后 `pgrep -af 'camera_publisher|ros2 launch ros2_trashbot_bringup bringup.launch.py'` 无残留。
- 本轮未发送 `/cmd_vel`，未启动底盘。

部署前结论：

- 远端安装尚未部署本轮 `/dev/video1` 默认值时，默认 camera smoke 不能作为通过证据。
- 本地软件侧默认固化已通过静态测试和 Docker/Humble 构建；真实上位机默认 smoke 仍需在部署本轮代码后复跑。

#### 4.1 只同步本轮 launch 文件到远端

同步命令：

```bash
scp -P 37878 onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py \
  onboard/src/ros2_trashbot_bringup/launch/learn.launch.py \
  root@192.168.1.11:/root/rober/onboard/src/ros2_trashbot_bringup/launch/
```

同步后默认值核对：

```text
/root/rober/onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py:117:
        'camera_device', default_value='/dev/video1',
/root/rober/onboard/src/ros2_trashbot_bringup/launch/learn.launch.py:74:
        'camera_device', default_value='/dev/video1',
```

hash 核对：

```text
cbb7bc8afca4d605b2f6edfc213c81a2034fa76eab1837d1a1f3d10ecf374045  /root/rober/onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py
1f2b65660f0f5567fe6a951ded3da36dc6ef4059a2a37f606067bd0d8406acfc  /root/rober/onboard/src/ros2_trashbot_bringup/launch/learn.launch.py
```

本轮只同步上述两个 launch 文件；未修改远端底盘、LiDAR、Nav2、任务编排、手机端或云端文件。

#### 4.2 远端最小重建

命令：

```bash
cd /root/rober/onboard
source /opt/ros/humble/setup.bash
source install/setup.bash
colcon build --symlink-install --packages-select ros2_trashbot_bringup
```

输出：

```text
Starting >>> ros2_trashbot_bringup
Finished <<< ros2_trashbot_bringup [0.72s]

Summary: 1 package finished [2.05s]
```

结论：远端 `ros2_trashbot_bringup` 最小重建通过。

#### 4.3 部署后不传 `camera_device` 复验通过

命令：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  camera_enabled:=true \
  camera_width:=640 \
  camera_height:=480 \
  camera_fps:=2.0
```

关键输出：

```text
== topic list ==
/amcl_pose
/camera/image_raw
/map
/parameter_events
/rosout
/trashbot/waypoints
== topic info ==
Type: sensor_msgs/msg/Image
Publisher count: 1
Subscription count: 0
== topic metadata sample ==
image_message_observed=true
height=480
width=640
encoding=bgr8
step=1920
data_len=921600
[camera_publisher-3] [INFO] [1781032906.084726950] [camera_publisher]: camera_publisher streaming /dev/video1 to /camera/image_raw with frame_id=camera, requested 640x480@2.00fps
== cleanup check ==
```

清理复核：

- smoke 结束后定向清理 `camera_publisher` 和 `ros2 launch ros2_trashbot_bringup bringup.launch.py`。
- 最终 `ps -eo pid=,args= | grep -E '[c]amera_publisher|[r]os2 launch ros2_trashbot_bringup bringup.launch.py'` 无输出。

结论：

- `default_camera_device_smoke_proven=true`：真实上位机部署本轮 launch 后，不显式传 `camera_device` 已默认使用 `/dev/video1` 并发布 `/camera/image_raw`。
- `software_proof_only=false`：本轮已有本地静态/Docker 软件证明和部署后真实上位机 no-motion smoke。
- `visible_content_proven=false` 仍成立：本轮只验证 topic metadata 和默认设备选择，不证明可见环境内容。
- `motion_commands_sent=false`：本轮未发送 `/cmd_vel`，未启动底盘运动。

### 5. 工作树状态

最终验收时运行：

```bash
git status --short
```

输出：

```text
 M docs/vision/board_camera_publisher.md
 M onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py
 M onboard/src/ros2_trashbot_bringup/launch/learn.launch.py
 M onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py
?? sprints/2026.06.10_03-10_board-camera-default-field-harden/tech-done.md
```

结论：本轮保留改动仅限允许范围内文件。

### 6. Patrol.idl / PythonLibs 构建失败复核

Robot Platform Engineer 于 2026-06-10 03:21 CST 继续复核前序不稳定失败点；未修改 Dockerfile、构建脚本、`ros2_trashbot_interfaces` 包元数据或 action/msg/srv 文件。

复跑 launch contract unittest：

```bash
python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py
```

输出：

```text
................
----------------------------------------------------------------------
Ran 16 tests in 0.025s

OK
```

复跑 Docker/Humble build：

```bash
bash onboard/scripts/docker_humble_build.sh
```

关键预检输出：

```text
Server: Docker Desktop 4.45.0 (203075)
ServerVersion=28.3.3 Driver=overlayfs DockerRootDir=/var/lib/docker
InvalidBaseImagePlatform: Base image osrf/ros:humble-desktop was pulled with platform "linux/amd64", expected "linux/arm64" for current build
WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8)
```

关键 build 输出：

```text
Starting >>> ros2_trashbot_interfaces
Finished <<< ros2_trashbot_interfaces [44.9s]
Finished <<< ros2_trashbot_bringup [6.22s]
Summary: 6 packages finished [55.4s]
```

补充定位命令：

```bash
docker run --rm -v "$PWD/onboard:/ws" -w /ws ros-rbs-humble:dev bash -lc '...'
docker run --rm ros-rbs-humble:dev bash -lc 'source /opt/ros/humble/setup.bash; cmake --find-package -DNAME=PythonLibs -DCOMPILER_ID=GNU -DLANGUAGE=C -DMODE=EXIST'
```

关键输出：

```text
build/ros2_trashbot_interfaces/rosidl_adapter/ros2_trashbot_interfaces/action/Patrol.idl
include=/usr/include/python3.10
LIBDIR=/usr/lib/x86_64-linux-gnu
LDLIBRARY=libpython3.10.so
PythonLibs found.
```

结论：本次复核中 `Patrol.idl` 丢失与 `Could NOT find PythonLibs` 均未复现；当前容器内 `Patrol.idl` 文件存在，Python 3.10 headers/libpython 路径存在，CMake `PythonLibs` 探测可通过。前序失败更符合 Docker Desktop 在 arm64 host 上运行 amd64 ROS Humble 镜像时的偶发生成/探测不稳定，而不是本轮相机默认值补丁造成的仓库回归。

## 剩余风险

- `software_proof_only=false`：本轮已完成本地软件验证和真实上位机部署后 no-motion smoke；但仍不是 HIL、运动或送达证明。
- `visible_content_proven=false`：默认设备固化不解决黑场或低亮度问题；不能把这路画面用于路线关键帧、视觉定位、障碍识别或远程可视验收。
- `safe_to_control=false`：本轮没有底盘运动、HIL、WAVE ROVER UART 或 Nav2 实跑证据。
- `delivery_success=false`：本轮没有验证送垃圾、到站、返回、投放或用户任务闭环。
- Docker/Humble 全量 build 已复核通过；但 Docker Desktop 仍提示 amd64 镜像运行在 arm64 host 上，后续偶发构建不稳定风险未完全消除。
- `/dev/video1` 是当前实板事实，不等于量产稳定命名方案；后续如设备枚举变化，仍需显式覆盖 `camera_device` 或另开 udev/设备探测任务。
- `visible_content_proven=true` 前，下一轮现场采集仍应先处理镜头盖、遮挡、朝向、光照和 USB 摄像头本体问题。

## 协同需求

- Product：需要在阶段验收时确认本轮只提升默认设备防误绑，不提升 OKR 完成度或视觉内容可用性。
- Hardware：后续仍需现场排查镜头盖、遮挡、朝向、光照和 USB 摄像头本体，目标是把 `visible_content_proven` 变为 true。
- Autonomy：路线 keyframe/视觉定位前必须等待可见内容证据，不能只凭 `/camera/image_raw` topic 存在进入路线视觉验收。
- Full-Stack：本轮不涉及手机/Web/API，无需协同。
