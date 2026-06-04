# Tech Done: Runtime Material Followup

## sprint_type

sprint_type: epic

## 实际改动

### Robot Software Engineer

- 修复 `onboard/scripts/o1_lidar_scan_proof_collector.py` 的 ROS2 CLI readiness false blocker：不再用 Humble 不支持的 `ros2 --version`，改为 `command -v ros2 && ros2 --help >/dev/null`。
- 更新 `onboard/scripts/test_o1_lidar_scan_proof_collector.py` 和 `docs/interfaces/lidar_ros2_closed_loop.md`。
- 记录 owner note：`owner_notes/robot-software-engineer.md`。

### Robot Algorithm Engineer

- 未改 vision 代码；新增 `owner_notes/robot-algorithm-engineer.md`。
- 本地和上位机均未找到真实/受控电梯 manifest 或图片候选；checker 保持 blocked。

### User Touchpoint Full-Stack Engineer

- PC direct-upper 新增 `GET /api/o7/direct-upper/operator-report` readback。
- operator-report POST/GET 允许现场默认 `http://192.168.1.11:8787`，仍只触达 `/api/operator/report`。
- 更新 PC UI 文案、server tests、`docs/interfaces/o7_direct_upper_pc_api.md`、`docs/product/pc_tools_workstation.md`。
- 记录 owner note：`owner_notes/full-stack-software-engineer.md`。

### Hardware Infra Engineer

- 未改硬件脚本；新增 `owner_notes/robot-hardware-engineer.md`。
- 读取 vendor 资料后完成 SSH 非运动 serial/status/preflight；fresh `/api/base/feedback-request` 观察到 `T=130 -> T=1001`。

## 验证结果

- Robot Software:
  - `python3 -m unittest onboard.scripts.test_upper_robot_api`：26 tests OK, 1 skipped。
  - `python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector`：5 tests OK。
  - `python3 -m compileall -q onboard/scripts`：通过。
  - SSH 上位机：8787 live、ROS2 package prefix 存在，但 graph 只有 `/parameter_events`、`/rosout`；radar/map/localize/nav2 hooks 返回 `dry_run_stub / no_command_configured`。
- Robot Algorithm:
  - 本地只找到 fixture manifest、采集模板、PGM fixture 和 UI 截图。
  - SSH 上位机只返回 `BASE=/root/rober`，无真实/受控电梯 manifest 或图片。
  - `--check-template` 输出 `status=blocked_missing_real_or_controlled_images`、`can_run_opencv_eval=false`、`real_or_controlled=0`。
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test`：20 tests OK。
- Full-Stack:
  - `cd pc-tools/workstation && npm test -- --run`：3 files / 98 tests passed。
  - `npm run build`：通过。
  - `npm run lint`：通过。
  - `GET http://192.168.1.11:8787/api/operator/report`：HTTP 200，且 `safe_to_control=false`、`robot_control_executed=false`、`sends_base_motion_commands=false`。
- Hardware:
  - inventory 只读：`/dev/ttyACM0` 仍按 STC/LiDAR 错口高风险处理。
  - `/dev/ttyS5` 存在但 `identity_insufficient`，仍需物理追线。
  - readiness：pyserial、ROS Humble setup、install setup 存在，`wave_rover_readiness=not_ready_for_control`。
  - dry-run HIL preflight：`dry_run_only`，`manual_request=null`，`safe_to_control=false`。
  - fresh 非运动 `T=130 -> T=1001`：`observed_feedback_types=[130,1001]`，`t1001_feedback_status=observed`，但 `robot_ack_connected=false`、`hil_pass=false`。

## 偏差和失败定位

- O2 root cause：缺真实/受控电梯图片 manifest。
- O3 root cause：live 8787 没有配置 radar/map/localize/Nav2 非运动 hook，ROS graph 没有应用 topic。
- O1 risk：fresh feedback endpoint 读到 `T=1001`，但 `/api/base/status` 仍可能显示 stale samples artifact；PC/status 层必须区分 `fresh_feedback_request` 和 `stale_feedback_samples_latest`。
- Full-Stack 初始 worker 超时，后续 verifier 完成验证并补 owner note。

## 剩余风险

- 不证明真实电梯识别、楼层 OCR、目标楼层确认、真实进出电梯或跨楼层送达。
- 不证明 fresh `/scan` once/hz、`/map`、AMCL、TF、Nav2 lifecycle 或 Nav2 消费 scan+map。
- 不证明 PC WASD 控车、`/api/base/manual`、robot ACK、HIL、`safe_to_control=true` 或 delivery success。
- LiDAR collector 修复尚需同步到上位机 filesystem，当前只是本地代码和 SSH stdin 临时验证。
