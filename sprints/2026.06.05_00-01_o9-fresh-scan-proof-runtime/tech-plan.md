# Tech Plan: O9 Fresh Scan Proof Runtime

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低 Objective：O9，当前 0%。
2. 本 sprint 针对最低 Objective：是。主目标是 O9 fresh scan proof runtime，同时支撑 O3 建图/定位/Nav2 前置材料和 O7 operator runtime readback。
3. 本 sprint 不重复消费 HTTP 405 或 `ros2_command_unavailable`：上一轮 `22-23_runtime-material-deploy-refresh` 已解除 live refresh route HTTP 405，并通过 ROS logging env guard 让 `ros2_available=true`。本轮聚焦 `upper_api_scan_not_proven` 收窄、missing `/scan` topics 和 LiDAR runtime/TF。

## Vendor 来源

- 必读入口：`docs/vendor/VENDOR_INDEX.md`。
- LiDAR ROS2 当前来源：`docs/vendor/lidar_pkg_ros2-main/`。
- 关键事实边界：vendor ROS2 LiDAR reference 发布 `/scan`，默认参数在 `config/lidar_params.yaml`，headless launch 在 `launch/lidar.launch.py`，driver/parser 在 `src/lidar_node.cpp`。本 sprint 不从记忆推断串口设备、topic、frame 或启动命令。

## 单 owner 实施计划

主责：Robot Software Engineer。

实施顺序：

1. 本地回归：先跑 upper API/collector 相关 unittest 与 compileall，确认本地合同没有回退。
2. 远端只读状态检查：SSH 到 `root@192.168.1.11 -p 37878`，检查 service、ROS2 CLI、ROS graph、`/scan`、`/lidar/raw_packet`、TF、LiDAR launch/device 状态。
3. 远端 scan smoke/refresh：只读或雷达启动相关 smoke 后，调用 live 8787 refresh/latest，确认 blocker 是否从 `upper_api_scan_not_proven` 收窄或消除。
4. 如需修复：只允许修改 live upper ROS2/LiDAR runtime、collector、bringup/launch、接口文档和本 sprint `tech-done.md`；不碰底盘运动、不发 `/cmd_vel`。
5. 记录证据：把命令、输出片段、artifact path、evidence_type、失败定位和剩余风险写入本 sprint `tech-done.md`。

## 允许文件范围

Robot Software Engineer 后续执行时允许改动：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/o1_lidar_scan_proof_collector.py`
- `onboard/scripts/test_upper_robot_api.py`
- `onboard/src/**/launch/**/*.py`
- `onboard/src/**/config/**/*.yaml`
- `docs/interfaces/lidar_ros2_closed_loop.md`
- `docs/interfaces/o7_upper_robot_api.md`
- `sprints/2026.06.05_00-01_o9-fresh-scan-proof-runtime/tech-done.md`

禁止范围：

- 不改底盘运动参数或硬件配置。
- 不改 PC UI，除非后续明确追加 Full-stack readback smoke。
- 不改 `OKR.md`。
- 不改既有 sprint 文件，尤其不覆盖 `sprints/2026.06.04_22-23_runtime-material-deploy-refresh/tech-done.md` 的旧 follow-up。

## 本地验收命令

Robot Software Engineer 必须运行并记录：

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
```

```bash
python3 -m compileall -q onboard/scripts onboard/src
```

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/test_upper_robot_api.py docs/interfaces/lidar_ros2_closed_loop.md docs/interfaces/o7_upper_robot_api.md sprints/2026.06.05_00-01_o9-fresh-scan-proof-runtime/tech-done.md
```

## 远端 read-only/status/smoke/refresh 命令

所有远端命令必须通过：

```bash
ssh root@192.168.1.11 -p 37878 '<command>'
```

Read-only/status：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; hostname; date -Is; systemctl is-active trashbot-upper-robot-api.service || true; curl -fsS http://127.0.0.1:8787/health; curl -fsS http://127.0.0.1:8787/api/radar/status; curl -fsS http://127.0.0.1:8787/api/radar/scan-proof/latest || true'
```

ROS2 graph and scan smoke：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; source /opt/ros/humble/setup.bash; if [ -f /root/rober/onboard/install/setup.bash ]; then source /root/rober/onboard/install/setup.bash; fi; ros2 topic list; ros2 topic info /scan || true; timeout 5 ros2 topic echo --once /scan || true; timeout 5 ros2 topic hz /scan || true; ros2 topic info /lidar/raw_packet || true; timeout 5 ros2 topic echo --once /lidar/raw_packet || true; timeout 5 ros2 run tf2_ros tf2_echo base_link laser_frame || true'
```

LiDAR runtime fact check：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; ls -l /dev/lidar /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true; pgrep -af "lidar|laser|scan" || true; source /opt/ros/humble/setup.bash; if [ -f /root/rober/onboard/install/setup.bash ]; then source /root/rober/onboard/install/setup.bash; fi; ros2 pkg list | grep -E "lidar|scan" || true'
```

Refresh route：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; curl -fsS -X POST http://127.0.0.1:8787/api/radar/scan-proof/refresh; echo; curl -fsS http://127.0.0.1:8787/api/radar/scan-proof/latest'
```

Safety boundary check：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; curl -fsS http://127.0.0.1:8787/api/base/status || true; curl -fsS http://127.0.0.1:8787/api/radar/status | grep -E "safe_to_control|scan_status|scan_proof|not_proven|blocked" || true'
```

## 验收判定

- Pass：latest artifact 可证明 fresh `/scan` once/hz 或 scan proof blocker 被具体收窄，且 `safe_to_control=false`，无 `/cmd_vel` 或底盘运动。
- Partial：HTTP 2xx 但仍有 `upper_api_scan_not_proven`，同时已定位到具体 LiDAR runtime root cause。
- Fail：仍只得到 `ros2_command_unavailable`、`upper_api_scan_not_proven`、missing `/scan` topics，且没有更具体原因。

## 风险边界

- 不把 HTTP 200、PC readback、按钮可点或计划文档写成 O9 完成。
- 不把 `/scan` 历史 artifact 写成 fresh proof。
- 不把 `T=1001`、base status 或 operator report 写成 robot ACK。
- 若 SSH 不可达、ROS2 环境不可 source、LiDAR device 不存在或 `/scan` 长期缺失，必须以 `blocked_with_root_cause` 留档并请求下一轮决策。
