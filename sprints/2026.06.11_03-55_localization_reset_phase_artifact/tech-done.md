# Localization Reset Phase Artifact

## sprint_type

micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：新增阶段性 partial artifact 写入，覆盖 `start`、`map_inputs`、`managed_runtime`、`initialpose`、`amcl_pose_probe`、`tf_probe`、`path_generation`、`cleanup`、`final` 等阶段；artifact 新增 `last_phase`、`last_successful_phase`、`phase_history`、`current_command`、`recent_commands`。
- `onboard/scripts/upper_robot_api.py`：helper timeout fallback 优先读取并保留 helper 已写 partial artifact，再追加 `helper_process_timeout_after_partial_artifact` root cause；`/api/localize/proof/latest` 顶层读回阶段字段。
- `onboard/tests/test_nav2_runtime_proof_helper.py`、`onboard/tests/test_upper_robot_api.py`：新增 partial artifact、timeout 合并和 latest readback 单元测试。
- `docs/navigation/fixed_route_workflow.md`、`docs/hardware/board_sensor_stack_smoke.md`：同步记录定位 reset 阶段证据链和 no-motion/不触碰底盘 UART 边界。

## 验证结果

- 本地单元测试：
  - 命令：`cd /Users/m1/apps/rober && python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：`Ran 37 tests in 2.166s`，`OK`。
- 本地语法检查：
  - 命令：`cd /Users/m1/apps/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 结果：通过，无输出。
- diff whitespace：
  - 命令：`cd /Users/m1/apps/rober && git diff --check`
  - 结果：通过，无输出。
- 真实上位机 smoke：
  - 部署：`scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/`，远端 `python3 -m py_compile` 通过，`trashbot-upper-robot-api.service` 重启后为 `active`。
  - 调用：`POST http://127.0.0.1:8787/api/localize/reset`，随后 `GET http://127.0.0.1:8787/api/localize/proof/latest`。
  - 本地 evidence：
    - `sprints/2026.06.11_03-55_localization_reset_phase_artifact/artifacts/remote_capture/localize_reset_response_final.json`
    - `sprints/2026.06.11_03-55_localization_reset_phase_artifact/artifacts/remote_capture/localize_proof_latest_final.json`
    - `sprints/2026.06.11_03-55_localization_reset_phase_artifact/artifacts/remote_capture/localization_reset_latest.final.remote.json`
    - `sprints/2026.06.11_03-55_localization_reset_phase_artifact/artifacts/remote_capture/final_process_device_check_final.log`
  - 关键字段：`status=blocked_with_root_cause`，`last_phase=interrupted`，`last_successful_phase=ros2_preflight`，`managed_runtime_started=true`，`initialpose_published=false`，`amcl_pose_observed=false`，`localization_tf_observed.map_to_odom=false`，`localization_tf_observed.map_to_base_link=false`。
  - root causes：`sigint_before_final_artifact`，`helper_process_timeout_after_partial_artifact`。
  - current command：`ros2 pkg prefix nav2_amcl`。
  - recent commands：`command -v ros2 && ros2 --help >/dev/null`、`ros2 pkg prefix ros2_trashbot_bringup`、`ros2 pkg prefix ros2_trashbot_nav`、`ros2 pkg prefix nav2_map_server` 均已记录且为 `ok=true`。
  - 清场：`final_process_device_check_final.log` 只输出 `active`，说明服务 active，目标 ROS 进程 grep 无输出，`lsof/fuser /dev/ttyS5 /dev/ttyACM0` 无占用输出。
  - 路径修正验证：远端 `/root/rober/runtime/localization_reset_latest.json` 不存在；canonical artifact 只保留 `/root/rober/onboard/runtime/localization_reset_latest.json`。

## 剩余风险

- 本轮已经解决 timeout 时 evidence chain 不够精确的问题，但没有让 AMCL/Nav2 定位成功。
- 当前真实上位机 blocker 是 helper 在外层 timeout 前仍卡在 package check 阶段，`current_command=ros2 pkg prefix nav2_amcl`；尚未到达 `/initialpose` 发布、`/amcl_pose` 或 TF probe。
- `managed_runtime_cleanup_ok=false` 来自 helper 被外层 SIGINT 打断前未进入自身 cleanup/final 阶段；外层清场证据显示目标 ROS 进程和 `/dev/ttyS5`、`/dev/ttyACM0` 最终无残留占用。
- 本轮不触碰 PC 普通用户首页，不改变 UI，不发送 `/cmd_vel`、`NavigateToPose` 或 WAVE ROVER 底盘 UART 命令。
