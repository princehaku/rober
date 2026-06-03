# O1 8787 Upper Robot API Base Feedback Request

## Endpoint

`POST /api/base/feedback-request`

该接口是 8787 统一上位机 API 的显式非运动反馈请求入口。调用时只向当前配置的 base serial port 写入一次 vendor `{"T":130}`，随后在短读取窗口内读取 newline-delimited JSON，统计是否观察到 `T=1001`。

`GET /api/status`、`GET /api/base/status` 不会自动触发该请求。

## Vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

已采用结论：

- WAVE ROVER UART 使用 UTF-8 JSON 行协议，以 `\n` 分帧。
- `CMD_BASE_FEEDBACK=130`，用于请求 base feedback。
- `FEEDBACK_BASE_INFO=1001`，是本接口观察的反馈类型。
- `T=1`、`T=13`、`T=131` 分别是运动或 feedback-flow 状态命令，本接口不得发送。

## Request Body

字段可省略：

```json
{
  "read_timeout_s": 0.2,
  "read_window_s": 1.2
}
```

实现会对窗口参数限幅，避免一次 HTTP 请求长期占用串口。

## Response Contract

关键字段：

- `schema=trashbot.upper_robot_api.v1.base_feedback_request_result`
- `vendor_sources[]`
- `serial_open`
- `serial_write`
- `serial_read`
- `read_line_count`
- `parsed_json_count`
- `invalid_json_count`
- `observed_feedback_types`
- `t1001_feedback_status`
- `feedback_ack`
- `blocked_commands_not_sent`

固定 fail-closed 字段：

- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

`feedback_ack.t1001_observed=true` 只表示本次短窗口中观察到 `T=1001` JSON 行。它不是 HIL pass，不能替代真实串口日志、ROS `/odom`、`/imu/data`、`/battery`、operator report 或完整上车验收。

## 2026-06-03 13-14 远端部署验证

本轮已把当前 `onboard/scripts/upper_robot_api.py` 通过 `scp` 部署到远端
`/root/rober/onboard/scripts/upper_robot_api.py`，并重启
`trashbot-upper-robot-api.service`。验证只调用非运动 endpoint：

```bash
POST http://127.0.0.1:8787/api/base/feedback-request
```

真实返回关键字段：

- HTTP `200`
- `serial_open.ok=true`
- `serial_write.command={"T":130}`
- `serial_write.bytes_written=10`
- `read_line_count=2`
- `parsed_json_count=2`
- `observed_feedback_types=[130,1001]`
- `t1001_feedback_status=observed`
- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `hil_pass=false`

本次验证没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、`T=131`
或 ROS `/cmd_vel`。一次 `T=1001` observed 只能证明 8787 feedback endpoint
已部署并能采到一帧真实反馈材料；仍不是 HIL pass，不能替代多帧同源反馈、
ROS `/odom`、`/imu/data`、`/battery`、自动停车/急停演练和 operator HIL report。
