# PC PWM Bridge Debug Manual Control

sprint_type: micro

## 实际改动

- PC 低速试动、首动复验和键盘连续手控统一改为 `command_mode=pwm`、`feedback_mode=bridge_debug`，继续保持普通用户简易界面和隐藏兼容确认字段。
- 上位机 `POST /api/base/manual` 增加 `bridge_debug` 反馈模式：非 ROS 手控只写低速命令和多模式停车命令，不直接抢读 `/dev/ttyS5`，反馈从 `esp32_bridge` 新鲜 debug log 回灌到 latest artifact 与顶层摘要。
- PC 手控代理补充从 `manual_feedback_samples_latest.t1001_feedback_frames` 提取 wheel raw 摘要，避免桥接反馈被直接串口读回缺失覆盖。
- 产品文档同步写明 ROS2 配套地图观察工具：普通用户用 `/map` 大屏，工程观察用 RViz2 或 Foxglove bridge。

## 验证结果

- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests`：通过，`Ran 93 tests`，`OK (skipped=1)`。
- `cd pc-tools/workstation && npm test -- catalog.test.ts`：通过，`Tests 183 passed`。
- `cd pc-tools/workstation && npm run build`：通过；仅保留 Vite 大 chunk 警告。
- 上位机 SSH `root@192.168.1.11 -p 37878` 可连；`GET http://127.0.0.1:8787/api/health` 返回 `status=ready`。
- 上位机运行参数已把手控 PWM 限幅压到 `manual_pwm_min_abs=90`、`manual_pwm_max_abs=90`；资料来源采用 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER vendor JSON 命令资料，控制命令使用 `T=11`，停车覆盖 `T=11/T=1/T=13`。
- PC Node 已重启并监听 `*:7001`；`GET http://127.0.0.1:7001/api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- PC 代理 `POST /api/robot-control/base/manual` 低速前进 `0.08m/s`、`400ms` 返回 `manual_command_executed=true`、`auto_stop_executed=true`。
- 直接上位机 PWM 复验返回 `base_command_mode=pwm`、`feedback_mode=bridge_debug`、`command_result.command={"T":11,"L":90,"R":90}`、`stop_result.command={"T":11,"L":0,"R":0}`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。
- 上位机脚本已重新 `scp` 到 `/root/rober/onboard/scripts/upper_robot_api.py` 并重启；重启后 PC 代理 250ms PWM 点动仍返回 `manual_command_executed=true`、`auto_stop_executed=true`。
- `GET /api/base/feedback-samples/latest` 返回 `motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`、`wheel_feedback_lr_nonzero_proven=false`。
- PC summary 读回 `keyboard_manual_command_mode=pwm`、`keyboard.readback.manual_command_mode=pwm`、地图可见、雷达地图点当前为 `123`、`move_now_status=ready_for_safety_confirm`、`nav2_route_run_status=ready_for_safety_confirm`。

## 剩余风险

- 现场 `T=1001` wheel raw `L/R` 在 speed 与 PWM 试动中仍可能保持 `0/0`；当前只能把 IMU 姿态变化作为次级运动信号，wheel raw 非零闭环仍需继续定位 WAVE ROVER 固件/反馈口径。
- 摄像头首帧仍指向 USB `12M` full-speed/物理链路问题，不是浏览器多人预览独占导致；需要换高速 USB 口/线或带供电 Hub 后复测。
- Nav2 完整路线执行仍需 HIL 收口；本轮只修 PC 手控/键盘底盘命令链路，不宣称完整自动驾驶已经验收。
