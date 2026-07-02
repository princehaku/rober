# PC 大地图与实时 WASD 手控

sprint_type: micro

## 实际改动

- PC 普通用户操作台继续保持简易风格，不改成工程调试台；地图默认缩放从 200% 提升到 300%，首屏优先给地图画布高度，保留最大 800% 缩放，避免当前窄地图源在 PC 上显得过小。
- `/api/robot-control/summary`、`/api/robot-control/live-summary` 与前端契约同步暴露 `map_display_default_zoom_percent=300%`，并说明 ROS2 配套工具是 RViz2 / Foxglove，属于工程观察入口，不替代普通用户 PC 主界面，也不会仅因打开地图触发运动。
- PC 普通手控与键盘连续手控改走 `feedback_mode=realtime`：上位机仍下发短 PWM 脉冲与 stop，但跳过每次按键前后的固定 GET 反馈快照，降低 WASD 连续操作延迟；松键/停止后的反馈仍由 summary 或 feedback-samples 入口读取。
- `upper_robot_api.py` 新增 `serial_write_only_realtime` 事务模式，实时手控不覆盖旧的 `manual_feedback_samples_latest`，避免把“跳过反馈采样”的短脉冲误写成 wheel raw L/R 证据。
- 文档同步更新 `docs/product/pc_tools_workstation.md` 与 `docs/navigation/fixed_route_workflow.md`，明确 PC 地图策略、ROS2 工程配套入口、实时 WASD 反馈边界与摄像头剩余风险。

## 硬件资料依据

- 已按硬件规则复读 `docs/vendor/VENDOR_INDEX.md`。
- 本轮涉及 WAVE ROVER UART/JSON 手控边界时，采用本地资料：
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：vendor Python 上位机以 `json.dumps(data) + '\n'` 写串口，示例 `/dev/ttyAMA0 @ 115200`，并提示 `/dev/serial0 @ 115200`；当前 Orange Pi 实板路径仍以项目既有现场证据 `/dev/ttyS5 @ 115200` 为准。
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h` 与 `uart_ctrl.h`：`T=1` 为速度控制，`T=11` 为 PWM 输入，`T=13` 为 ROS 控制，`T=130/131/142/143` 为反馈/流控/echo 相关命令，底盘反馈类型包含 `T=1001`。
- 本轮没有改串口设备、波特率、接线、电压、固件或 WAVE ROVER command ID；只改变 PC 快速手控时是否在每个短脉冲内等待固定反馈快照。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests`：通过，97 个测试通过，1 个跳过。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts test/catalog.test.ts test/robotControlSummary.test.ts`：通过，3 个测试文件、431 个测试通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 构建产物生成；仅保留 chunk size 警告。
- `bash onboard/scripts/docker_humble_build.sh`：通过，Docker/Humble 内 `colcon build --symlink-install` 完成，`Summary: 6 packages finished [46.9s]`。
- 实板部署：已通过 `ssh root@192.168.1.11 -p 37878` 更新 `/root/rober/onboard/scripts/upper_robot_api.py`，并重启为 `python3 scripts/upper_robot_api.py --host 0.0.0.0 --port 8787`。
- PC API：已重启本地 `pc-tools/workstation` API 到 `0.0.0.0:7001`，`/api/health` 返回 `workstation_listen_address=http://0.0.0.0:7001` 与默认小车 API `http://192.168.1.11:8787`。
- 实时手控 smoke：
  - 直接请求小车 `POST http://192.168.1.11:8787/api/base/manual`，`feedback_mode=realtime`、`command_mode=pwm`、`manual_command_executed=true`、`auto_stop_executed=true`，耗时约 314ms。
  - 经 PC 代理 `POST http://127.0.0.1:7001/api/robot-control/base/manual`，`proxy_status=command_forwarded`、远端 HTTP 200、`manual_command_executed=true`、`auto_stop_executed=true`，耗时约 457ms。
- 地图/摘要 smoke：
  - `/api/robot-control/summary` 与 `/api/robot-control/live-summary` 均返回 `map_display_default_zoom_percent=300%`、`map_display_primary_url=/map`、`map_display_ros2_companion_tools=["rviz2","foxglove"]`。
  - `/api/robot-control/map/preview` 能加载地图摘要，当前源图尺寸为 `261x113`，目标点可见；这说明 PC 侧“地图显小”的主要原因是源图很窄，默认 300% 与更高画布高度是当前 UI 侧的保守修复。
- `git diff --check`：通过。

## 剩余风险

- 摄像头仍不是本轮修复完成项。现有证据显示 `/dev/video1` 在 12M USB full-speed 下 `VIDIOC_STREAMON` I/O error，`source_usage_status=not_in_use`，更像物理 USB 速率/线缆/口问题，不是单纯独占；软件共享预览入口保留，但真实画面还需要现场换高速 USB 口/线后复测。
- 实时 WASD 为了手感跳过每个短脉冲的 before/after 固定反馈快照，因此 PC 代理 smoke 仍会声明 `wheel_feedback_lr_nonzero_not_proven`。松键后读取 feedback-samples 或 summary 才能作为 wheel raw L/R 证据。
- RViz2/Foxglove 是 ROS2 工程配套工具，适合看 TF、LaserScan、Path、Costmap、Nav2 状态；普通用户 PC 主界面仍应保持简易大地图，不应把 RViz2 复杂界面直接暴露给普通用户。
