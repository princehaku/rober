# PC WASD Bridge Feedback Window

## sprint_type

micro

## 实际改动

- 修复 `onboard/scripts/upper_robot_api.py` 的 `/api/base/manual` ROS/bridge_debug 手控读回链路：当 `esp32_bridge` 已持有 UART 并持续写 fresh `wave_rover_feedback_debug.jsonl` 时，把 bridge-owned vendor `T=1001` 帧挂回本次 `feedback_during_motion`，避免 PC first-jog/WASD 结果误显示执行窗口 `T1001` 帧数为 0。
- 新增 `bridge_debug_summary_as_manual_feedback_payload()`，该函数只转换已有 debug JSONL，不打开串口、不发送额外 `T=130`，并保持 `safe_to_control=false`、`delivery_success=false`、`hil_pass=false`。
- 更新 `onboard/scripts/test_upper_robot_api_free_roam.py`，覆盖 ROS 手控成功、反馈由 bridge debug JSONL 提供、`L/R=0/0` 仍不通过 wheel 非零但执行窗口能看到 T1001 帧的场景。
- 修复 `pc-tools/workstation/src/server/index.ts` 的 `remote_motion_key_values` 提取逻辑：优先读取上位机顶层 `feedback_during_motion` / `feedback_evidence`，旧 `serial_motion_transaction.*` 只作为兼容 fallback，确保 PC first-jog/WASD 摘要不再误显示执行窗口 0 帧。
- 更新 `pc-tools/workstation/test/catalog.test.ts`，让 first-jog 代理测试只提供顶层 `feedback_during_motion`，并断言 `feedback_during_motion_status/source` 被抬到 PC 摘要。
- 更新 `docs/hardware/wave_rover_json_bridge.md` 与 `docs/product/pc_tools_workstation.md`，说明 PC WASD/first-jog 现在能显示 bridge-owned 执行窗口反馈帧，同时不把 `L/R=0/0`、IMU 姿态变化或命令到达升级成 wheel 非零、HIL pass、Nav2 成功或 delivery success。

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

采用口径：WAVE ROVER UART 为换行 JSON；`T=11` 是 PWM direct，`T=13` 是 ROS ctrl 且 vendor 标注不适用于无编码器产品；底盘反馈帧为 vendor `T=1001`，字段含 `L/R/r/p/y/v`。

## 验证结果

- `python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam.UpperRobotApiFreeRoamTest.test_ros_manual_control_reports_bridge_feedback_as_motion_window`：通过。
- `python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam`：通过，`Ran 11 tests`。
- `npm test -- --run test/catalog.test.ts -t "Robot Control first-jog proxy exposes raw during-motion L/R key values"`：通过，`1 passed`。
- `npm test -- --run test/catalog.test.ts`（`pc-tools/workstation`）：通过，`184 passed`。
- `npm run build`（`pc-tools/workstation`）：通过；Vite 仍提示单个 chunk 大于 500 kB 的既有体积 warning。
- 上位机部署：`scp -P 7878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py` 后重启 `trashbot-upper-robot-api.service`，服务监听 `0.0.0.0:8787`，`/api/health` 返回 `status=ready`。
- PC 7001 重启后复测：`POST /api/robot-control/base/first-jog?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=command_forwarded`、`manual_command_executed=true`、`auto_stop_executed=true`、`feedback_during_motion_t1001_frame_count=80`、`feedback_during_motion_source=esp32_bridge_feedback_debug_log`、`wheel_feedback_latest_raw_left/right=0/0`、`wheel_feedback_lr_nonzero_proven=false`。

## 剩余风险

- 本轮修复的是 PC/上位机对执行窗口反馈材料的归因问题，不改变底盘物理行为。现场最近 first-jog 已能发送 `T=11,L/R=255` 并自动 stop，但 vendor `T=1001.L/R` 仍为 `0/0`。
- 摄像头仍卡在 UVC `12M` full-speed 拓扑，`VIDIOC_STREAMON` 返回 `Input/output error`；这不是页面独占问题，需要换高速 USB 口/线或带供电 USB Hub 后复测。
- 自动驾驶/完整 Nav2 route 仍不能声明完成，直到 action result、同窗口运动材料、wheel raw 或明确 operator/HIL 材料满足验收。
