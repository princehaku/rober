# Robot Software Engineer Note

## sprint_type

micro

## 当前中止状态

- 用户在部署脚本同步完成后中止本轮，要求立即停止继续探索并汇报。
- 本轮已完成远端文件备份与同步，但尚未执行 8787 reload/restart。
- 因未 reload/restart，当前 live `POST /api/radar/scan-proof/refresh` 仍应视为未验收，不能推动 O3/O7 涨分。

## 已读文件

- `AGENTS.md`
- `OKR.md`
- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/test_upper_robot_api.py`
- `onboard/scripts/upper_robot_api.sh`
- `docs/interfaces/o7_upper_robot_api.md`
- `docs/interfaces/lidar_ros2_closed_loop.md`
- `sprints/2026.06.04_21-22_runtime-material-runtime-hooks/tech-plan.md`
- `sprints/2026.06.04_21-22_runtime-material-runtime-hooks/tech-done.md`
- `sprints/2026.06.04_21-22_runtime-material-runtime-hooks/final.md`
- `sprints/2026.06.04_21-22_runtime-material-runtime-hooks/owner_notes/robot-software-engineer.md`

## 本地改动

- 新增本文件：`sprints/2026.06.04_22-23_runtime-material-deploy-refresh/owner_notes/robot-software-engineer.md`
- 未改动本地 `onboard/scripts/upper_robot_api.py`、`onboard/scripts/test_upper_robot_api.py`、`onboard/scripts/o1_lidar_scan_proof_collector.py`、`docs/interfaces/o7_upper_robot_api.md`、`docs/interfaces/lidar_ros2_closed_loop.md`。

## 远端已执行部署动作

- SSH 目标：`root@192.168.1.11 -p 37878`
- 远端 8787 当前进程曾被定位为：
  - PID `30042`
  - 命令：`python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`
- systemd unit 存在但当时 inactive：
  - `/etc/systemd/system/trashbot-upper-robot-api.service`
  - `ExecStart=/usr/bin/env bash /root/rober/onboard/scripts/upper_robot_api.sh`
  - `Active: inactive (dead) since Thu 2026-06-04 18:19:07 CST`
- 远端旧脚本检查结果：
  - `/root/rober/onboard/scripts/upper_robot_api.py`
  - `sha256=068208c7376d45a82e3e9d7fc1e4688eb77dddfa281ae034b4ab43e6834f09e8`
  - `has_refresh_route=false`
- 已同步到远端的脚本：
  - `/root/rober/onboard/scripts/upper_robot_api.py`
  - `/root/rober/onboard/scripts/o1_lidar_scan_proof_collector.py`
- 远端备份目录：
  - `/root/rober/runtime/deploy_backups/20260604T221619+0800`
- 远端安装输出：
  - `upper_robot_api.py` old sha256 `068208c7376d45a82e3e9d7fc1e4688eb77dddfa281ae034b4ab43e6834f09e8`
  - `upper_robot_api.py` new sha256 `c1b6fc0c1f7141e5da1c5c80de71462889ea77e39085ed11b07b59f90d97dfd6`
  - `o1_lidar_scan_proof_collector.py` old sha256 `3918ae0d4884ac4952ef4ee1bfc0473b2f9bdcdd55bfb4e5de624cbb18b8d2d8`
  - `o1_lidar_scan_proof_collector.py` new sha256 `b27621eb19e27d57e2fb907ddfa87f9c181cd65c77f10f5182626350bf285ee4`
  - `verify_compile.returncode=0`

## 已运行验证命令与结果

- `python3 -m unittest onboard.scripts.test_upper_robot_api`
  - 输出：`Ran 28 tests in 1.966s`
  - 结果：`OK (skipped=2)`
- `python3 -m compileall -q onboard/scripts`
  - 结果：通过，无输出。
- `git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/o7_upper_robot_api.md docs/interfaces/lidar_ros2_closed_loop.md sprints/2026.06.04_22-23_runtime-material-deploy-refresh/owner_notes/robot-software-engineer.md`
  - 结果：通过，无输出。
- SSH live pre-check：
  - `GET /health` -> HTTP `200`
  - `GET /api/radar/status` -> HTTP `200`
  - `POST /api/radar/scan-proof/refresh` -> HTTP `405`, body `405: Method Not Allowed`
  - `GET /api/radar/scan-proof/latest` -> HTTP `200`

## 未执行动作

- 未 reload/restart 8787。
- 未再次 POST refresh 验证。
- 未执行任何底盘运动控制。
- 未调用 `/cmd_vel`、`/api/base/manual`。
- 未发送 WAVE ROVER `T=1/T=13/T=130/T=131`。
- 未把 `safe_to_control` 置为 true。

## 当前判断

- 当前卡点不是本地代码缺 route，而是远端 8787 运行进程仍加载旧代码。
- 远端文件已同步为新版，但因为还没有 restart/reload，live route 仍未验收。
- 下一步若继续，建议只对精确匹配的 8787 upper API 进程做安全重启，优先用 systemd 启动 `trashbot-upper-robot-api.service`，再验证四个只读 live endpoints。

## 继续执行：精确重启与只读 endpoint 复测

- 执行时间：2026-06-04 22:24 CST。
- 重启前只读确认 PID `30042`：
  - argv：`python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`
  - cwd：`/root`
  - selected env 仅见 `PATH`；argv 已直接定位 `/root/rober/onboard/scripts/upper_robot_api.py`。
- unit 匹配结果：
  - `trashbot-upper-robot-api.service` 指向 `/root/rober/onboard/scripts/upper_robot_api.sh`。
  - unit 环境为 `HOST=0.0.0.0`、`PORT=8787`、`ROBER_CAMERA_BASE_URL=http://127.0.0.1:8088`、`ROBER_BASE_SERIAL_PORT=/dev/ttyS5`、`ROBER_BASE_BAUDRATE=115200`、`ROBER_BASE_MAX_SPEED=0.12`。
  - 因 unit 当时 `inactive (dead)`，不能用 `systemctl stop` 接管游离 PID；本轮只对已精确匹配的 upper API PID `30042` 发送 `SIGTERM`，未使用 `kill -9`，未处理未知进程。
- restart/reload 方法：
  - `SIGTERM` 精确停止 PID `30042`。
  - 等待 `:8787` 端口释放。
  - `systemctl start trashbot-upper-robot-api.service`。
  - systemd 启动返回 `returncode=0`，unit 进入 `active (running)`，Main PID `38154`。
  - 同一条启动脚本里即时 `ss` 未抓到 listen，导致该脚本最终返回 `5`；随后 HTTP 复测证明 8787 已正常监听。

## 继续执行：HTTP live 复测

- `GET /health`
  - HTTP `200`
  - `schema=trashbot.upper_robot_api.v1.health`
  - `status=ready`
  - `safe_to_control=false`
- `GET /api/radar/status`
  - HTTP `200`
  - `schema=trashbot.upper_robot_api.v1.radar_status`
  - `scan_status=not_proven`
  - `observed_lidar_port=/dev/ttyACM0`
  - `controls.scan_proof_refresh.endpoint=/api/radar/scan-proof/refresh`
  - `controls.scan_proof_refresh.starts_driver=false`
  - `controls.scan_proof_refresh.opens_lidar_serial=false`
  - latest artifact path：`runtime/lidar_scan_proof_latest.json`
  - latest artifact status：`loaded`
- `POST /api/radar/scan-proof/refresh`
  - HTTP `200`
  - `schema=trashbot.upper_robot_api.v1.lidar_scan_proof_refresh_result`
  - `status=refreshed`
  - `proof_state=blocked_or_not_observed`
  - `evidence_type=blocked_with_root_cause`
  - `artifact_path=runtime/lidar_scan_proof_latest.json`
  - `safe_to_control=false`
  - `sends_commands=false`
  - `sends_motion_commands=false`
  - `robot_control_executed=false`
  - `opens_lidar_serial=false`
  - `starts_lidar_driver=false`
  - `proof_summary.scan_once_observed=false`
  - `proof_summary.scan_hz_observed=false`
  - `proof_summary.raw_packet_once_observed=false`
  - `proof_summary.tf_observed=false`
  - `proof_summary.all_required_observations_observed=false`
  - blockers：
    - `ros2_command_unavailable`: `ros2 command is unavailable in the current environment`
    - `upper_api_scan_not_proven`: `8787 radar scan_status='not_proven'`
- `GET /api/radar/scan-proof/latest`
  - HTTP `200`
  - `schema=trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result`
  - artifact path：`runtime/lidar_scan_proof_latest.json`
  - artifact status：`loaded`
  - artifact ok：`true`
  - `proof_status=blocked_or_not_observed`
  - `all_required_observations_observed=false`
  - blockers count：`2`

## 继续执行后的结论

- 部署/路由问题已解除：live `POST /api/radar/scan-proof/refresh` 不再是 `405`，当前返回 HTTP `200`。
- 本轮仍不能涨 O3/O7 runtime 分：refresh 的 root cause 是远端当前 API 进程环境 `ros2_command_unavailable`，所以 artifact fresh readback 只能证明只读 refresh route 可执行并写出 blocked root cause，不能证明 `/scan`、hz、raw packet 或 TF 已被观察到。
- 本轮没有触碰底盘运动链路：未调用 `/cmd_vel`、`/api/base/manual`，未发送 WAVE ROVER `T=1/T=13/T=130/T=131`，未打开底盘串口，未把 `safe_to_control` 置为 true。

## 继续执行：ROS log env fix 与最新 live refresh

- 执行时间：2026-06-04 23:20-23:25 CST。
- 本地代码修复：
  - `onboard/scripts/o1_lidar_scan_proof_collector.py`
    - 新增 ROS2 CLI 前置环境：`HOME=${HOME:-/root}`、`USER=${USER:-root}`、`LOGNAME=${LOGNAME:-root}`、`ROS_HOME=${ROS_HOME:-$HOME/.ros}`、`mkdir -p "$ROS_HOME/log"`、`ROS_LOG_DIR=${ROS_LOG_DIR:-$ROS_HOME/log}`。
    - 原因：`trashbot-upper-robot-api.service` 进程环境缺 `HOME/USER/LOGNAME/ROS_LOG_DIR`，ROS2 topic read 会先在 rcl logging 初始化阶段失败，掩盖真实 `/scan` topic 状态。
    - 安全边界：该修复只影响 ROS2 CLI 日志目录和 artifact 诊断字段，不启动 LiDAR driver、不打开 `/dev/ttyACM0`、不打开 `/dev/ttyS5`、不发送 `A5 60`、不发送 WAVE ROVER `T=1/T=13/T=130/T=131`、不发布 `/cmd_vel`。
  - `onboard/scripts/test_o1_lidar_scan_proof_collector.py`
    - 新增 regression test，确保 collector 生成的 ROS2 CLI 命令保留 systemd-safe logging environment。

- 本地验证：
  - `python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector`
    - 输出：`Ran 6 tests in 0.594s`
    - 结果：`OK`
  - `python3 -m unittest onboard.scripts.test_upper_robot_api`
    - 输出：`Ran 28 tests in 1.798s`
    - 结果：`OK (skipped=2)`
  - `python3 -m compileall -q onboard/scripts`
    - 结果：通过，无输出。

- 远端备份/同步：
  - 备份目录：`/root/rober/runtime/deploy_backups/20260604T232019+0800_ros_log_env`
  - 回滚文件：`/root/rober/runtime/deploy_backups/20260604T232019+0800_ros_log_env/o1_lidar_scan_proof_collector.py`
  - 备份旧 hash：`b27621eb19e27d57e2fb907ddfa87f9c181cd65c77f10f5182626350bf285ee4`
  - 同步后本地 hash：`7175ec89c6ebcc18bca22414f58029cd3504aaecdd1b4bb0aa11d376ddb1d3c4`
  - 同步后远端 hash：`7175ec89c6ebcc18bca22414f58029cd3504aaecdd1b4bb0aa11d376ddb1d3c4`
  - 远端 `python3 -m py_compile /root/rober/onboard/scripts/o1_lidar_scan_proof_collector.py`：通过，无输出。
  - 未重启 8787：upper API 每次 refresh 以 subprocess 方式执行 collector，本次只替换 collector 文件即可生效。

- 最新 live `POST /api/radar/scan-proof/refresh`：
  - HTTP `200`
  - `schema=trashbot.upper_robot_api.v1.lidar_scan_proof_refresh_result`
  - `status=refreshed`
  - `proof_state=blocked_or_not_observed`
  - `evidence_type=blocked_with_root_cause`
  - `artifact_path=runtime/lidar_scan_proof_latest.json`
  - `latest_result.generated_at=2026-06-04T15:24:52.896869Z`
  - `latest_result.generated_at_ms=1780586667853`
  - `ros2_available=true`
  - `ros2_cli_check.ok=true`
  - `ros_log_dir_default=/root/.ros/log`
  - `scan_once_observed=false`
  - `scan_hz_observed=false`
  - `raw_packet_once_observed=false`
  - `tf_observed=false`
  - `all_required_observations_observed=false`
  - `blockers_summary`：
    - `upper_api_scan_not_proven`: `8787 radar scan_status='not_proven'`
  - topic read failure details after log env fix:
    - `/scan` once：`WARNING: topic [/scan] does not appear to be published yet`，`Could not determine the type for the passed topic`
    - `/lidar/raw_packet` once：`WARNING: topic [/lidar/raw_packet] does not appear to be published yet`，`Could not determine the type for the passed topic`
    - `/scan` hz：collector subprocess timeout after `7.0s`
    - TF：`Invalid frame ID "base_link" ... frame does not exist`
  - 安全字段：`safe_to_control=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`starts_lidar_driver=false`、`opens_lidar_serial=false`、`sends_lidar_start_command=false`
  - 明确未发送：`A5 60`、`T=1`、`T=13`、`T=130`、`T=131`、`/cmd_vel`、`/api/base/manual`
  - 明确未打开：`/dev/ttyS5`、`/dev/ttyACM0`、`/dev/lidar`

- 最新 live `GET /api/radar/scan-proof/latest`：
  - HTTP `200`
  - `schema=trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result`
  - artifact：`runtime/lidar_scan_proof_latest.json`
  - artifact status：`loaded`
  - artifact ok：`true`
  - artifact bytes：`18346`
  - `latest_result.generated_at=2026-06-04T15:24:52.896869Z`
  - `proof.status=blocked_or_not_observed`
  - `ros2_available=true`
  - `scan_once_observed=false`
  - `scan_hz_observed=false`
  - `raw_packet_once_observed=false`
  - `tf_observed=false`
  - `safe_to_control=false`
  - `robot_control_executed=false`

- 最新结论：
  - 旧 blocker `HTTP 405` 已解除。
  - 中间 blocker `ros2_command_unavailable` / ROS logging directory crash 已解除；现在 artifact 能看到 `ros2_available=true`，并且 ROS2 CLI 命令包含 `ROS_LOG_DIR=/root/.ros/log` 兜底。
  - 当前剩余 blocker 是真实 runtime 未启动或未发布 `/scan`、`/lidar/raw_packet` 与 `base_link -> laser_frame` TF；本次 refresh 按合同只读 existing topics，不启动 driver，因此不能把该结果写成 fresh scan proof。
  - 本轮仍不能推动 O3/O7 产品 Objective 涨分，只能作为 deployment/runtime blocker 进一步收敛证据。
