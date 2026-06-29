# ROS 手控 bridge 反馈回灌

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`：`summarize_bridge_feedback_debug_log` 现在保留 compact `T=1001` 帧列表，并优先使用 bridge 写出的 `vendor_frame.L/R/r/p/y/v` 原始字段。
- `onboard/scripts/upper_robot_api.py`：ROS 手控/PC 键盘 pulse 成功后，不直接打开 `/dev/ttyS5` 抢 UART；如果 esp32_bridge feedback debug JSONL 是 fresh 且有 `T=1001`，只读该日志并包装成 `base_feedback_samples_latest`，供 PC summary 显示 wheel raw L/R。
- `onboard/tests/test_upper_robot_api.py`：新增 ROS 手控复用 fresh bridge feedback 的单测，并隔离旧 motion window/keyboard 用例对真实上位机日志的依赖。
- `docs/hardware/wave_rover_json_bridge.md`：同步记录 ROS 手控/键盘短 pulse 的 bridge-owned feedback 边界。

## 验证结果

- 本地 focused：`python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_manual_control_ros_persists_fresh_bridge_feedback_without_opening_uart onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_manual_control_default_motion_window_tracks_pulse_duration onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_manual_control_keyboard_pulse_keeps_short_motion_window onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_bridge_feedback_debug_log_summarizes_latest_wheel_raw`，结果 `Ran 4 tests ... OK`。
- 本地全量：`python3 -m unittest onboard.tests.test_upper_robot_api`，结果 `Ran 86 tests ... OK`。
- 上位机同步：已通过 `scp -P 37878` 同步 `onboard/scripts/upper_robot_api.py` 与 `onboard/tests/test_upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/`。
- 上位机单测：`ssh root@192.168.1.11 -p 37878 'bash -lc "cd /root/rober/onboard && python3 tests/test_upper_robot_api.py"'`，结果 `Ran 86 tests in 1.094s ... OK`。
- 上位机 API：已用同参数重启 `upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`，`ss -ltnp` 显示 `0.0.0.0:8787` 由新 `python3` 进程监听。
- PC 只读 summary：本机 `node` 仍监听 `*:7001`；`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 可读到 `base_status=loaded`、当前 wheel `L/R=0/0`、`wheel_feedback_lr_nonzero_proven=false`。

## 剩余风险

- 本轮未触发真实手控、键盘、Nav2 发车或 `/cmd_vel` 运动命令；需要用户在现场安全确认后再跑一次 ROS 手控/键盘或 Nav2 路线，复验 fresh bridge 日志里的 `T=1001 L/R` 是否非零。
- 该回灌只解决“PC 看不到 ROS 手控期间 wheel raw L/R 证据”的软件链路问题，不证明摄像头首帧、完整自动驾驶到达或 delivery success。
