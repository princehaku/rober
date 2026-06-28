# 2026.06.29 04:20 PC keyboard ROS bridge no UART contention

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 底盘反馈解析新增 `parse_serial_json_objects()`：现场 UART 行可能是合法 `{"T":1001,...}` 后粘连 `\r` 和损坏碎片，现在会提取完整 JSON 对象，不再整行误判 invalid。
  - `feedback_request_status()` 新增 `observed_with_read_error`：读到 T1001 后如果后续串口 `SerialException`，保留“已观测反馈但读阶段有错误”的部分成功状态。
  - 默认 `command_mode=ros` 的 `/api/base/manual` 改为发布短时 `/cmd_vel` 到 `/esp32_bridge`，pulse 到时后发布零速 `/cmd_vel`；不再直开 `/dev/ttyS5` 与 bridge 抢串口。
  - `command_mode=pwm/speed` 仍保留为显式诊断 override，继续走旧串口事务和运动中 T1001 采样。
  - ROS bridge 手控路径不写新的 wheel latest artifact，因为它不直接读 UART，避免用“未采集”覆盖旧 wheel 材料。
- `onboard/tests/test_upper_robot_api.py`
  - 新增真实噪声形态回归：合法 T1001 + 损坏尾巴必须解析出 T1001。
  - 新增 T1001 已观测后 late read error 的状态回归。
  - 更新 manual 默认路径测试：默认 ROS 手控不再调用 `manual_motion_serial_transaction()`，而是调用 `manual_motion_ros_cmd_vel_transaction()`。
  - 保留 PWM 显式诊断模式的串口采样测试。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步说明 PC 键盘连续手控和 Nav2 默认复用 `/esp32_bridge`，浏览器仍只调用固定 PC 代理，不直连 `/cmd_vel`。

## 验证结果

- 本地通过：`python3 -m unittest onboard.tests.test_upper_robot_api`，75 tests OK。
- 本地通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py`。
- 本地通过：`git diff --check`。
- 本地通过：`npm test -- --run test/App.test.ts -t "keyboard|manual|base/manual|safety"`，28 tests passed / 182 skipped。
- 真车只读确认：`fuser/lsof /dev/ttyS5` 显示当前 holder 是 `esp32_bridge`，ROS node list 包含 `/esp32_bridge` 和 `/free_roam_autonomy`。
- 真车非运动验证：部署第一版解析修复后，`POST /api/base/feedback-request` 第 3 次在仍有 `SerialException` 的情况下读到 `parsed_json_count=2`、`observed_feedback_types=[1001]`、`t1001_frame_count=2`、latest wheel raw L/R 为 `0/0`，安全字段 `sends_motion_commands=false`、`robot_control_executed=false`、`safe_to_control=false`。
- 真车部署：已同步 `upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`，并重启 `trashbot-upper-robot-api.service`。
- 真车服务修正：发现旧 `upper_robot_api.py --host 0.0.0.0 --port 8787` 孤儿进程占用端口，导致 systemd 新服务反复重启失败；已仅清理该旧 API 进程并启动 systemd 服务，未停止 `/esp32_bridge`、`/free_roam_autonomy`、雷达 lifecycle、Nav2 goal、manual 或 `/cmd_vel`。
- 真车非运动复验：新进程下 4 次 `POST /api/base/feedback-request` 中，读到 T1001 的窗口分别返回
  `observed_with_read_error`、`observed`、`observed_with_read_error`；其中一次完整窗口为
  `parsed_json_count=6`、`observed_feedback_types=[1001]`、`t1001_frame_count=6`、`read_error_type=null`。
  全部复验均保持 `sends_motion_commands=false`、`robot_control_executed=false`、`safe_to_control=false`。

## 剩余风险

- 本轮没有执行真实 manual/keyboard 发车、Nav2 goal、free-roam start、delivery 或 `/cmd_vel` HIL；默认 ROS bridge 手控路径只做代码和 mock 验证。
- 现场 UART 仍存在间歇性 `SerialException` 和坏行；解析已能 salvage 完整 T1001，但稳定反馈闭环还需要后续从 `esp32_bridge` 侧 debug log 或 topic readback 收敛。
- wheel raw L/R 本轮只在非运动反馈里恢复到可解析 `0/0`，还没有证明运动中 L/R 非零。
