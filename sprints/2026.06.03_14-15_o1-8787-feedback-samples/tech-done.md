# 2026.06.03 14-15 O1 8787 Feedback Samples

## sprint_type

micro

## 目标

推进当前最低 Objective 1：在 8787 上位机 Robot API 中新增保守的非运动多样本 feedback evidence collector。目标不是 HIL pass，也不是 motion/manual；目标是把一次 `T=130 -> T=1001` observed 推进为可重复、多样本、同源采集入口和材料记录。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 已证实的硬件结论

- WAVE ROVER vendor 上位机参考使用 UART、UTF-8 JSON、每行一个 JSON 对象并以 `\n` 结束。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130` 和 `FEEDBACK_BASE_INFO=1001`。
- `uart_ctrl.h` 的 `CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`。
- `ugv_advance.h` 的 `baseInfoFeedback()` 输出 `T=1001`，包含 `L/R/r/p/y/v` 等字段并 `Serial.println(...)`。
- `T=1`、`T=13`、`T=131` 分别属于运动或 feedback-flow 状态命令，本轮未发送。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `POST /api/base/feedback-samples`。
  - 新增 `trashbot.upper_robot_api.v1.base_feedback_samples_result` schema。
  - 新增 `sample_count`、`sample_interval_s`、`read_timeout_s`、`read_window_s` 限幅。
  - 复用 `request_base_feedback_once()`，每个 sample 只发送 vendor `{"T":130}`。
  - 聚合 `requested_sample_count`、`completed_sample_count`、`samples[].t1001_feedback_status`、`t1001_observed_count`、`observed_feedback_types`、`all_samples_observed_t1001`、`partial_samples_observed_t1001` 和 `feedback_ack.t1001_observed`。
  - 修正 ACK 证据边界：`feedback_ack.t1001_observed` 保留 observed 语义，但 `feedback_ack.robot_ack_connected` 固定为 `false`，reason 明确 `T=1001` 只是 vendor feedback material，不证明项目层 robot ACK/HIL。
  - 新增 `ROUTE_PATHS` 路由 registry，`/api/status` routes 和实际 aiohttp route registration 共用。
- `onboard/scripts/test_upper_robot_api.py`
  - 覆盖多样本成功解析。
  - 覆盖部分 sample 未观察到 `T=1001` 时仍 fail-closed。
  - 覆盖单次和多样本 observed 时 `t1001_observed=true` 但 `robot_ack_connected=false`。
  - 覆盖 `feedback-samples` route registry 存在，且 `base_status()` 不触发串口采样。
- `docs/interfaces/o1_upper_robot_api_base_feedback.md`
  - 新增 `/api/base/feedback-samples` contract、request/response schema 和远端 3/3 samples 结果。
- `docs/interfaces/o7_upper_robot_api.md`
  - 更新 endpoint 表、安全边界和 2026-06-03 实测结果。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 更新多样本 collector 的 vendor 证据链、接口边界和远端验证材料。
- `docs/process/okr_progress_log.md`
  - 追加本轮 O1 14-15 micro sprint 进度日志。
- `sprints/2026.06.03_14-15_o1-8787-feedback-samples/tech-done.md`
  - 本轮 micro sprint 留档。

## 本地验证结果

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_upper_robot_api.py
...........
----------------------------------------------------------------------
Ran 11 tests in 0.864s

OK
```

```text
$ python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py
exit 0
```

```text
$ git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/o1_upper_robot_api_base_feedback.md docs/interfaces/o7_upper_robot_api.md docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/process/okr_progress_log.md sprints/2026.06.03_14-15_o1-8787-feedback-samples/tech-done.md
exit 0
```

## 远端部署与非运动采集结果

SSH 可达：

```text
$ timeout 8 ssh -o BatchMode=yes -o ConnectTimeout=5 -p 37878 root@192.168.1.11 'echo ssh_ready'
ssh_ready
```

部署：

```text
$ scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py
exit 0
```

重启：

```text
$ ssh root@192.168.1.11 -p 37878 'systemctl restart trashbot-upper-robot-api.service && systemctl is-active trashbot-upper-robot-api.service'
active
```

只调用新的非运动 endpoint：

```text
$ ssh root@192.168.1.11 -p 37878 'python3 - <<"PY" ... POST http://127.0.0.1:8787/api/base/feedback-samples ... PY'
{
  "all_samples_observed_t1001": true,
  "blocked_commands_not_sent": [
    "T=1",
    "T=13",
    "T=131",
    "cmd_vel",
    "/api/base/manual"
  ],
  "completed_sample_count": 3,
  "delivery_success": false,
  "feedback_ack": {
    "reason": "T=1001 observed in 3/3 samples; this is vendor feedback material, not project robot ACK or HIL proof",
    "robot_ack_connected": false,
    "t1001_observed": true
  },
  "hil_pass": false,
  "http_status": 200,
  "observed_feedback_types": [
    130,
    1001
  ],
  "partial_samples_observed_t1001": false,
  "requested_sample_count": 3,
  "robot_control_executed": false,
  "safe_to_control": false,
  "sample_observed_types": [
    [
      130,
      1001
    ],
    [
      130,
      1001
    ],
    [
      130,
      1001
    ]
  ],
  "sample_statuses": [
    "observed",
    "observed",
    "observed"
  ],
  "schema": "trashbot.upper_robot_api.v1.base_feedback_samples_result",
  "sends_motion_commands": false,
  "t1001_observed_count": 3
}
```

## 安全声明

本轮没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、`T=131` 或 ROS `/cmd_vel`。远端业务调用只访问 `POST /api/base/feedback-samples`，该 endpoint 每个 sample 只发送 vendor `{"T":130}`。

## 剩余风险

- 3/3 个 `T=130 -> T=1001` sample 只证明同源非运动 vendor feedback material 可重复采集，不是 robot ACK connected，也不是 HIL pass。
- 仍未证明 `safe_to_control=true`、闭环安全控制、真实 `/odom`、`/imu/data`、`/battery`、自动停车/急停现场演练或 delivery success。
- 后续如要进入 `/api/base/manual` 或 ROS `/cmd_vel`，必须另行满足现场看护、物理净空、人工急停路径和 operator report。
- LiDAR 真实 `/scan`、`/lidar/raw_packet` 和 TF smoke 仍未由本轮覆盖。
