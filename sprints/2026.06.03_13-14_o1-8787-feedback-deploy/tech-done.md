# O1 8787 Feedback Deploy Micro Sprint

## sprint_type: micro

Owner: Hardware Infra Engineer

目标：关闭远端 `POST /api/base/feedback-request` HTTP 405 部署缺口，把已存在的本地
8787 feedback request 合同部署到上位机，并只用非运动 `T=130` 采集一次真实
`T=1001` feedback 材料。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

采用结论：

- WAVE ROVER 上下位机链路为 UART UTF-8 newline-delimited JSON。
- `CMD_BASE_FEEDBACK=130`，用于请求 base feedback。
- `FEEDBACK_BASE_INFO=1001`，是本轮观察的反馈类型。
- `T=1`、`T=13`、`T=131` 和 ROS `/cmd_vel` 属于运动或 feedback-flow 相关命令，本轮不得发送。

## 实际改动

- 远端部署：已通过 `scp` 将本地 `onboard/scripts/upper_robot_api.py` 复制到
  `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`。
- 远端服务：已重启 `trashbot-upper-robot-api.service`，`systemctl is-active` 返回 `active`。
- 本地文档：
  - `docs/interfaces/o7_upper_robot_api.md`：更新远端 feedback endpoint 405 已关闭和 HTTP 200 证据。
  - `docs/interfaces/o1_upper_robot_api_base_feedback.md`：补充 13-14 远端部署验证字段。
  - `docs/hardware/o1_wave_rover_serial_feedback_probe.md`：更新 `/dev/ttyS5 @115200` 上一次 `T=130 -> T=1001` observed 边界。
  - `docs/process/okr_progress_log.md`：追加本 micro sprint 进度记录。
  - `OKR.md`：最小修正明显笔误和当前 O1/O7 旧 405 口径。

## 验证结果

本地回归：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_upper_robot_api.py
```

输出片段：

```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.813s

OK
```

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py
```

输出片段：无输出，exit 0。

远端部署与状态：

```text
scp onboard/scripts/upper_robot_api.py -> /root/rober/onboard/scripts/upper_robot_api.py
systemctl restart trashbot-upper-robot-api.service
systemctl is-active trashbot-upper-robot-api.service
```

输出片段：

```text
active
```

远端 `/health`：

```text
{"schema":"trashbot.upper_robot_api.v1.health","status":"ready",...,"safe_to_control":false,"robot_control_executed":false}
```

远端 `/api/status` 片段：

```text
camera.status=ready
radar.observed_lidar_port=/dev/ttyACM0
base.port=/dev/ttyS5
safe_to_control=false
```

非运动 feedback endpoint：

```bash
POST http://127.0.0.1:8787/api/base/feedback-request
```

真实返回关键字段：

```text
HTTP/1.1 200 OK
serial_open.ok=true
serial_write.command={"T":130}
serial_write.bytes_written=10
serial_read.ok=true
read_line_count=2
parsed_json_count=2
invalid_json_count=0
observed_feedback_types=[130,1001]
t1001_feedback_status=observed
safe_to_control=false
sends_motion_commands=false
robot_control_executed=false
delivery_success=false
hil_pass=false
```

## 运动命令声明

本轮没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、`T=131`，
没有发送 ROS `/cmd_vel`。本轮唯一触达底盘串口的命令是非运动
feedback request `{"T":130}`。

## 剩余风险

- 一次 `T=1001` observed 不是 HIL pass，也不是 `safe_to_control=true`。
- 仍缺多帧同源 `T=1001`、operator report、自动停车/急停现场演练、真实 ROS
  `/odom`、`/imu/data`、`/battery` 和完整 HIL packet。
- LiDAR 真实 `/scan`、`/lidar/raw_packet` 和 TF smoke 仍未完成。
- 后续如果执行 `/api/base/manual`，必须在现场看护、物理净空、人工急停路径确认后进行，并采集 manual/stop/post-status 同源证据。
