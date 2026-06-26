# 2026-06-27 19:05 Nav2 PWM Execution Feedback

sprint_type: micro

## 实际改动

- 修复 `onboard/scripts/o11_nav2_goal_execution_proof.py`：O11 托管 `esp32_bridge` 从旧的
  `command_mode=speed` 改为当前真机已证明可动的 `command_mode=pwm`，并固定
  `pwm_min_abs=90`、`pwm_max_abs=90`。
- O11 执行时通过 `feedback_debug_log_path` 记录 WAVE ROVER `T=1001` 左右轮反馈，并新增
  `base_feedback_summary`。只有 `NavigateToPose` succeeded 且同轮左右轮反馈出现非零样本时，
  才写 `hil_pass=true` 与 `nav2_goal_execution_proven=true`。
- PC 固定 Nav2 execute/latest 代理同步放行该 endpoint 的执行证据字段：
  `sends_base_motion_commands=true`、`uses_base_uart=true`、`hil_pass=true`。仍继续阻断
  `safe_to_control=true`、`primary_actions_enabled=true`、`delivery_success=true`。
- 更新 `docs/interfaces/ros_runtime_contracts.md` 与 `docs/product/pc_tools_workstation.md`，说明
  Nav2 执行 proof 的 PWM 底盘路径、反馈证明边界和 PC fail-closed 口径。
- O11 托管 Nav2 runtime 改为 `map_server + static map->odom + esp32_bridge odom->base_link`，
  不再启动 `lidar_driver` 或 AMCL；`FollowPath.use_collision_detection=false`，避免当前路线执行 proof
  被雷达/局部 costmap 误障碍卡死。
- `esp32_bridge` 新增 `command_debug_log_path`，把 `/cmd_vel` 到 WAVE ROVER vendor JSON 的映射写成
  JSONL；PC latest 暴露 `base_command_*` 短字段，区分 Nav2 未发命令和底盘反馈未跟随。
- Camera MJPEG 共享预览保持 PC Node 单路上游 relay，多浏览器 fanout；上车 8088 MJPEG 使用 1s
  首帧预算，8787 代理增加 `sock_read=8s`，避免摄像头无帧时普通页面长期等待。
- 已部署到 `root@192.168.1.11:37878` 并重启
  `trashbot-local-webrtc-camera.service`、`trashbot-upper-robot-api.service`；PC Node API 重新绑定到
  `0.0.0.0:7001`。

## 验证结果

- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/upper_robot_api.py` 通过。
- `python3 onboard/tests/test_o11_nav2_goal_execution_proof.py` 通过，4 tests。
- `python3 onboard/tests/test_nav2_params_contract.py` 通过，1 test。
- `cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Nav2 execution"` 通过，2 tests。
- 远端 `python3 -m py_compile /root/rober/onboard/scripts/local_webrtc_camera_smoke.py /root/rober/onboard/scripts/upper_robot_api.py /root/rober/onboard/scripts/o11_nav2_goal_execution_proof.py` 通过。
- 远端直接 O11：`status=goal_succeeded`、`goal_accepted=true`、执行层 lifecycle active、
  `base_command_nonzero_observed=true`、`base_command_nonzero_count=50`、
  `base_feedback_sample_count=236`、`base_feedback_nonzero_sample_count=0`。
- PC 7001 固定 execute：HTTP 200，`proxy_status=execution_forwarded`，远端 artifact
  `status=goal_succeeded`、`base_command_mode=pwm`、
  `base_command_nonzero_observed=true`、`base_command_nonzero_count=49`、
  `base_feedback_lr_nonzero_proven=false`、`hil_pass=false`。
- Camera 复测：8088/8787 health 均为 HTTP 200，选中 `/dev/video1`；
  summary 显示 `source_usage_status=not_in_use`、`source_usage_owner_count=0`、
  `shared_preview_shared_capture=true`、`shared_preview_exclusive_camera_claim=false`。
  8787 `/api/camera/mjpeg` 在约 7 秒内 fail-closed 502，PC 7001 MJPEG 代理同样返回 502。
- `bash onboard/scripts/docker_humble_build.sh` 通过，`colcon build --symlink-install` 输出
  `Summary: 6 packages finished [43.3s]`。
- `git diff --check` 通过。

## 剩余风险

- 本次软件修复不能保证现场路线安全；真实执行仍需要现场确认空间、急停和安全勾选。
- 如果车上已有旧的 learn/Nav2/lidar 进程占用串口，O11 托管 runtime 可能启动失败；执行前需要清理或确认
  runtime 状态。
- Nav2/bridge 已发非零 PWM vendor JSON，但本轮 WAVE ROVER `T=1001 L/R` 仍为 `0/0`；
  不能声明 `hil_pass`、真实轮速闭环或 delivery success。
- 摄像头不可见不是 PC 独占：当前 blocker 是 `/dev/video1` 可枚举但无真实首帧输出；
  需要检查摄像头输入、USB 线/供电、采集卡模式或换 known-good UVC。
