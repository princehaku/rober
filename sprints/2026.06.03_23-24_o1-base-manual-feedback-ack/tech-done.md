# 2026.06.03 23-24 O1 Base Manual Feedback ACK

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 修复 `/api/base/manual` 响应证据链：方向 `T=1` 写入后仍先 auto-stop，再在 stop 成功后通过同一 `base_port/base_baudrate` 执行一次 vendor `T=130` 反馈请求。
  - 将 stop 后读取到的 `T=1001` 材料放入 `feedback_ack`、`t1001_feedback_status`、`feedback_evidence`、`feedback_after_stop_attempted`。
  - 若方向写入或 stop 写入失败，保留 `command_result`、`stop_result`、`serial_write_failures`，并返回 `skipped_due_to_manual_write_failure`，不追加反馈请求、不包装成功。
- `onboard/scripts/test_upper_robot_api.py`
  - 用 fake serial 覆盖 manual 成功路径：forward 点动按 `T=1 -> T=1 stop -> T=130` 顺序写入，并解析 fake `T=1001`。
  - 覆盖 manual 写失败路径：失败时不发送 `T=130`，仍保留结构化写失败。
- `docs/interfaces/o7_upper_robot_api.md`
  - 同步 `/api/base/manual` 的 stop 后 `T=130 -> T=1001` evidence 字段和 fail-closed 边界。

## 验证结果

- `python3 -m unittest onboard/scripts/test_upper_robot_api.py`
  - `Ran 16 tests in 1.527s`
  - `OK`
- `python3 -m compileall -q onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py`
  - 通过，无输出。

2026-06-04 00-01 复验：

- `python3 -m unittest onboard/scripts/test_upper_robot_api.py`
  - `Ran 16 tests in 1.428s`
  - `OK`
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py`
  - 通过，无输出。
- 当前 dirty diff 合理：manual 成功路径按 `T=1 -> stop -> T=130` 采 stop 后
  feedback evidence；方向写入或 stop 写入失败时 `feedback_after_stop_attempted=false`，
  不追加 `T=130`，不把失败包装成 ACK/HIL。

## 剩余风险

- 本轮只使用 fake serial 单元测试，没有打开真实 `/dev/ttyS5`，不等于 HIL pass。
- `T=1001` 仍只是 vendor feedback material，不等于项目 robot ACK connected、闭环安全控制或 `safe_to_control=true`。
- 真实现场仍需在物理净空、人工急停可用、operator 看护条件下复跑 `/api/base/manual`，采集 forward/back/left/right/stop 响应、post-status 和日志材料。

## 已读 vendor 来源与协议事实

- `docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER 上下位机链路为 UART newline-delimited UTF-8 JSON；Orange Pi 串口路径必须以现场确认为准，不能沿用 Raspberry Pi 默认。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - vendor `base_speed_ctrl()` 使用 `{"T":1,"L":...,"R":...}` 左右轮速度控制，参考 baudrate 为 `115200`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `CMD_SPEED_CTRL=1`，`CMD_BASE_FEEDBACK=130`，`FEEDBACK_BASE_INFO=1001`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - `CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`，即 `T=130` 是请求底盘反馈的 vendor 命令。
