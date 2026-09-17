# O1 8787 Upper Robot API Base Feedback Request

## Endpoint

`POST /api/base/feedback-request`

该接口是 8787 统一上位机 API 的显式非运动反馈请求入口。调用时只向当前配置的 base serial port 写入一次 vendor `{"T":130}`，随后在短读取窗口内读取 newline-delimited JSON，统计是否观察到 `T=1001`。

`POST /api/base/feedback-samples`

该接口是同源多样本 feedback evidence collector。它重复调用同一条 vendor `{"T":130}` 路径，每个 sample 都只发送一次 `T=130`，随后用短窗口读取 newline-delimited JSON，并聚合每个 sample 的 `T=1001` 观察状态。该接口不调用 `/api/base/manual`，不发送 `T=1`、`T=13`、`T=131` 或 ROS `/cmd_vel`。

`GET /api/base/feedback-samples/latest`

该接口只读回放最近一次 `/api/base/feedback-samples` 写入的 JSON artifact。它不打开串口、不 import/use pyserial、不发送 `T=130`、`T=1`、`T=13`、`T=131`、`cmd_vel` 或 `/api/base/manual`。artifact 不存在或 JSON 损坏时 fail-closed，返回结构化错误和固定安全字段。

`GET /api/status`、`GET /api/base/status` 不会自动触发 feedback request；两者会通过
`base.feedback_samples_latest` 暴露 latest artifact 的只读摘要和材料新鲜度。该摘要只做
`stat/read_text/json.loads`，不打开串口、不 import/use pyserial、不发送 `T=130` 或任何
motion/manual 命令。

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

### `/api/base/feedback-request`

字段可省略：

```json
{
  "read_timeout_s": 0.2,
  "read_window_s": 1.2
}
```

实现会对窗口参数限幅，避免一次 HTTP 请求长期占用串口。

### `/api/base/feedback-samples`

字段可省略：

```json
{
  "sample_count": 3,
  "sample_interval_s": 0.2,
  "read_timeout_s": 0.2,
  "read_window_s": 1.2
}
```

限幅：

- `sample_count`：`1..8`，默认 `3`。
- `sample_interval_s`：`0..2`，默认 `0.2`。
- `read_timeout_s`：复用单次 endpoint 限幅，默认 `0.2`。
- `read_window_s`：复用单次 endpoint 限幅，默认 `1.2`。

artifact path：

- CLI 参数：`--feedback-samples-artifact-path`
- 环境变量：`ROBER_BASE_FEEDBACK_SAMPLES_ARTIFACT_PATH`
- 默认：`runtime/base_feedback_samples_latest.json`

写入采用同目录临时文件 + `os.replace()` 原子替换。artifact 写入失败不会让采样结果冒泡成 HIL 或 safe-to-control；响应会在 `artifact.write` 中暴露失败原因。

### `/api/base/feedback-samples/latest`

无 request body。该接口只读取配置的 artifact path，不打开硬件。

### `/api/base/status` / `/api/status` status summary

无 request body。`base.feedback_samples_latest` 是 latest artifact 的轻量摘要，不等同于
`GET /api/base/feedback-samples/latest` 的完整 payload 回放；它面向 PC/运维首屏，默认
`stale_after_ms=900000`（15 分钟）。这个窗口只表示材料文件的新鲜度，不是 HIL、ACK、
`safe_to_control` 或可运动准入。

## Response Contract

### `/api/base/feedback-request`

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

`feedback_ack.t1001_observed=true` 只表示本次短窗口中观察到 `T=1001` JSON 行。`feedback_ack.robot_ack_connected` 必须保持 `false`，因为 vendor base feedback material 不等于项目层 robot ACK/HIL。它不是 HIL pass，不能替代真实串口日志、ROS `/odom`、`/imu/data`、`/battery`、operator report 或完整上车验收。

### `/api/base/feedback-samples`

关键字段：

- `schema=trashbot.upper_robot_api.v1.base_feedback_samples_result`
- `requested_sample_count`
- `completed_sample_count`
- `samples[]`
- `samples[].t1001_feedback_status`
- `samples[].observed_feedback_types`
- `t1001_observed_count`
- `observed_feedback_types`
- `all_samples_observed_t1001`
- `partial_samples_observed_t1001`
- `feedback_ack.t1001_observed`
- `blocked_commands_not_sent`
- `artifact.path`
- `artifact.write.ok`
- `artifact.write.method=atomic_replace`

固定 fail-closed 字段：

- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

多样本 observed 只能证明同一个 8787 非运动入口可以重复采到 vendor `T=1001` 材料。`feedback_ack.robot_ack_connected` 必须保持 `false`，因为重复观察 `T=1001` 仍不证明项目层 robot ACK/HIL。它仍不是 HIL pass，不能替代运动命令安全、真实 ROS `/odom`、`/imu/data`、`/battery`、自动停车/急停演练或完整上车验收。

### `/api/base/feedback-samples/latest`

关键字段：

- `schema=trashbot.upper_robot_api.v1.base_feedback_samples_latest_result`
- `artifact.status=loaded|missing|bad_json|json_not_object|read_failed`
- `latest_result`
- `latest_endpoint_path=/api/base/feedback-samples/latest`
- `readback_sends_commands=false`

固定 fail-closed 字段：

- `safe_to_control=false`
- `sends_commands=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

`latest_result` 是上一次 POST 采样的历史 payload，因此其中可能保留历史 `sends_commands=true`。顶层 `sends_commands=false` 和 `readback_sends_commands=false` 才表示本次 GET latest 行为没有发送任何命令。

### `/api/base/status` 与统一 `/api/status`

`base.feedback_samples_latest` 关键字段：

- `schema=trashbot.upper_robot_api.v1.base_feedback_samples_latest_summary`
- `endpoint=/api/base/feedback-samples/latest`
- `artifact.status=loaded|missing|bad_json|read_failed|json_not_object|unknown`
- `artifact.ok`
- `artifact.path`
- `artifact.configured_by`
- `artifact.mtime_ms`
- `artifact.updated_at_ms`（artifact 内可用时）
- `artifact.age_ms`
- `freshness.status=fresh|stale|missing|bad_json|read_failed|json_not_object|unknown`
- `freshness.stale_after_ms=900000`
- `latest_t1001_observed_count`
- `latest_all_samples_observed_t1001`
- `readback_sends_commands=false`
- `sends_commands=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `hil_pass=false`

`freshness.status=fresh` 只表示 latest artifact 文件在 15 分钟窗口内更新；`stale` 只表示材料
可能过旧。两者都不能证明当前串口在线、WAVE ROVER ACK、HIL pass、真实 ROS feedback topic、
manual control 或 `safe_to_control=true`。

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

## 2026-06-03 14-15 远端多样本验证

本轮继续只调用非运动 endpoint：

```bash
POST http://127.0.0.1:8787/api/base/feedback-samples
```

请求体：

```json
{
  "sample_count": 3,
  "sample_interval_s": 0.2,
  "read_timeout_s": 0.2,
  "read_window_s": 1.2
}
```

真实返回关键字段：

- HTTP `200`
- `schema=trashbot.upper_robot_api.v1.base_feedback_samples_result`
- `requested_sample_count=3`
- `completed_sample_count=3`
- `t1001_observed_count=3`
- `observed_feedback_types=[130,1001]`
- `all_samples_observed_t1001=true`
- `partial_samples_observed_t1001=false`
- `samples[].t1001_feedback_status=["observed","observed","observed"]`
- `samples[].observed_feedback_types=[[130,1001],[130,1001],[130,1001]]`
- `feedback_ack.t1001_observed=true`
- `feedback_ack.robot_ack_connected=false`
- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

本次验证没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、`T=131`
或 ROS `/cmd_vel`。该材料把一次 observed 推进为 3/3 多样本同源 observed；
但仍不能写成 robot ACK connected、HIL pass、闭环安全控制、真实 ROS feedback topic 或 delivery success。

## 2026-06-03 15-16 latest artifact readback 验证

本轮继续只调用非运动 POST 和只读 GET：

```bash
POST http://127.0.0.1:8787/api/base/feedback-samples
GET  http://127.0.0.1:8787/api/base/feedback-samples/latest
```

POST 真实返回关键字段：

- HTTP `200`
- `requested_sample_count=3`
- `completed_sample_count=3`
- `t1001_observed_count=3`
- `observed_feedback_types=[130,1001]`
- `all_samples_observed_t1001=true`
- `samples[].t1001_feedback_status=["observed","observed","observed"]`
- `artifact.write.ok=true`
- `artifact.write.bytes_written=4989`
- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `hil_pass=false`
- `feedback_ack.robot_ack_connected=false`

GET latest 真实返回关键字段：

- HTTP `200`
- `schema=trashbot.upper_robot_api.v1.base_feedback_samples_latest_result`
- `artifact.status=loaded`
- `latest_result.schema=trashbot.upper_robot_api.v1.base_feedback_samples_result`
- `latest_result.t1001_observed_count=3`
- `latest_result.all_samples_observed_t1001=true`
- `readback_sends_commands=false`
- `safe_to_control=false`
- `sends_commands=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `hil_pass=false`

本次验证没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、`T=131`
或 ROS `/cmd_vel`。latest readback 只证明 artifact 可读取，不证明它本身发送过或可以发送命令。

## 2026-09-18 可中断反馈采集

反馈请求已纳入单实例串口仲裁，阻塞 I/O 在专用线程运行。并发普通请求返回 HTTP `409`、`accepted=false`、`error.type=serial_busy`，不排队发送命令；Stop 可抢占读窗口。

`feedback-request` 与 manual 停车后的普通反馈见到有效 `T=1001` 即结束。`read_window_s` 为最大观察窗口；`read_timeout_s` 仍限制等待，实际每个读片额外限制在 `50 ms` 内，跨读片的 JSON 行会累计到换行再解析。早返回之后尚未读取的其他反馈不会计入 `observed_feedback_types`。

`feedback-samples` 保留显式完整窗口材料统计；批内等待可被 Stop/请求取消中断，新增顶层 `preempted`。被抢占时只记录已经采到的材料，`completed_sample_count` 可能小于请求数，`all_samples_observed_t1001=false`，采样结果中的 `serial_read.interrupted` 表示窗口未完整结束。持久化不占用串口 owner，避免慢盘延迟停车。所有 `robot_ack_connected`、`safe_to_control`、`hil_pass` 证据边界保持不变。

API 退出及 HTTP 取消会等待已接受动作的停车收口。该机制只覆盖此实例内部；真实部署中其他串口驱动仍需与它互斥。验证使用 fake UART，无真实运动或串口读写。
