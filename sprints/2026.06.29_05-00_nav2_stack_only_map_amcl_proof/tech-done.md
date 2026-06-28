# 2026-06-29 05:00 Nav2 stack-only 地图/AMCL/path proof

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`：`nav2_stack_only` 现在可按参数启动/复用底盘 bridge、LiDAR driver 和 `base_link->laser_frame` static TF，不再只拉 Nav2 bringup 后缺 `/scan`。
- `onboard/scripts/o11_nav2_lifecycle.sh`：新增 `--base-enabled auto`、`--lidar-enabled auto`、LiDAR 串口参数和 static laser TF 参数；检测到已有 `/esp32_bridge` 或 `/dev/ttyS5` holder 时不会再开第二个 bridge，检测到已有 `/scan` 或 `/dev/ttyACM0` holder 时不会抢雷达串口。
- `onboard/src/ros2_trashbot_nav/config/nav2_params.yaml`：补 `map_server.ros__parameters.yaml_filename` 占位，允许 Nav2 bringup 用 `map:=...` 正确重写地图；AMCL 默认 `set_initial_pose=true` 并使用地图原点，避免启动后没有 `map->odom`。
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：TF fallback 探针从 4s/5.5s 放宽到 10s/14s，匹配 Orange Pi 上 `ros2 run tf2_ros tf2_echo` 的真实启动/清理耗时，避免把可观测 TF 误判成 timeout。
- `onboard/scripts/upper_robot_api.py`：默认 Nav2 start command 接入上述 auto 参数；no-motion proof/goal helper 在复用外部 Nav2 runtime 时不再清理外部 lifecycle 残留，避免 proof 超时后误杀正在运行的 `lidar_driver`/Nav2 stack。
- 测试同步覆盖 launch 合同、lifecycle auto 复用、Nav2 参数合同、Robot API 命令校验和外部 runtime cleanup 边界。

硬件口径采用本地资料：`docs/vendor/VENDOR_INDEX.md`、WAVE ROVER UART/JSON command 资料，以及项目既有 `/dev/ttyS5@115200`、LiDAR `/dev/ttyACM0@150000` 现场证据。本轮没有修改 Clash 或系统代理；PC Node 仍应使用项目自身 `0.0.0.0:7001`，车上 Robot API 仍为 `0.0.0.0:8787`。

## 验证结果

- 本地：`python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper onboard.tests.test_upper_robot_api onboard.tests.test_o11_nav2_lifecycle_script onboard.src.ros2_trashbot_bringup.test.test_launch_contract_static onboard.tests.test_nav2_params_contract` 通过，144 tests OK。
- 本地：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py && bash -n onboard/scripts/o11_nav2_lifecycle.sh && git diff --check` 通过。
- 真实上位机：已同步改动到 `root@192.168.1.11:37878`，`python3 -m py_compile` 和 `bash -n` 通过，`trashbot-upper-robot-api.service=active`。
- 真实上位机 no-motion start 后读回：`map_server=active`、`amcl=active`、`planner_server=active`、`controller_server=active`；`/map` publisher=1、`/scan` publisher=1；`/amcl_pose` frame 为 `map`；`tf2_echo map base_link` 可读。
- 真实上位机 `POST /api/nav2/proof/refresh` no-motion path proof：`latest_proof_status=nav2_no_motion_path_generation_runtime_observed`、`latest_path_generation_succeeded=true`、`latest_path_point_count=18`、`latest_map_server_active=true`、`latest_amcl_active=true`、`latest_planner_active=true`、`latest_controller_active=true`、`latest_scan_consumed=true`、`latest_map_consumed=true`。安全字段保持 `safe_to_control=false`、`robot_control_executed=false`、`sends_base_motion_commands=false`、`delivery_success=false`。
- 摄像头现场复核：`/api/camera/health` 显示 `shared_preview_contract=single_shared_capture_for_multiple_clients`、`source_usage.owner_count=0`、`status=uvc_no_frame_not_exclusive`。结论是当前不是页面独占，而是 `/dev/video1` DV20 UVC 没有输出首帧。

## 剩余风险

- 本轮证明到 Nav2 runtime 和 no-motion path generation，尚未执行 NavigateToPose、未发布 `/cmd_vel`，因此还不是完整路线执行、wheel raw L/R 非零或 delivery success 证明。
- AMCL 默认初始位姿是地图原点；真实路线执行前仍应通过 PC initialpose/定位刷新覆盖到现场实际位置。
- 相机共享链路已在，但真实画面仍依赖 DV20 UVC 输出首帧；若继续无画面，需要检查 USB 摄像头输入、供电或换 known-good UVC 复测。
