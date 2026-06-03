# 2026.06.03 16-17 O1 feedback status summary tech-done

## sprint_type

micro

## 已读资料与 vendor 来源

- `AGENTS.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

采用的硬件事实：

- WAVE ROVER 上下位机链路是 UART UTF-8 JSON，一行一个 JSON 对象，以 `\n` 分帧。
- `CMD_BASE_FEEDBACK=130` 是非运动 feedback request。
- `FEEDBACK_BASE_INFO=1001` 是本轮 latest artifact 摘要读取的历史反馈类型。
- `T=1`、`T=13`、`T=131` 分别属于运动控制或 feedback-flow 状态命令，本轮 status summary 不发送。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `summarize_feedback_samples_latest_artifact(path, stale_after_ms=900000)`。
  - summary 只做 `Path.stat()`、`Path.read_text()`、`json.loads()`，不 import/use pyserial，不打开 `/dev/*`，不发送 `T=130/T=1/T=13/T=131/cmd_vel` 或 `/api/base/manual`。
  - `GET /api/base/status` 增加 `feedback_samples_latest`，统一 `GET /api/status` 的 `base.feedback_samples_latest` 同步可消费。
  - 摘要字段包含 endpoint、artifact status/ok/path/config source、`mtime_ms`、`updated_at_ms`、`age_ms`、`freshness.status`、`latest_t1001_observed_count`、`latest_all_samples_observed_t1001` 和固定 fail-closed 控制字段。
- `onboard/scripts/test_upper_robot_api.py`
  - 覆盖 `base_status()` 不打开 fake serial。
  - 覆盖 latest summary 的 fresh、stale、missing、bad_json、json_not_object。
  - 断言 summary/readback 均不发送命令、不执行控制。
- `docs/interfaces/o1_upper_robot_api_base_feedback.md`
  - 补齐 status summary contract 和 15 分钟 freshness 边界。
- `docs/interfaces/o7_upper_robot_api.md`
  - 补齐 `/api/status` 与 `/api/base/status` 的 `base.feedback_samples_latest` 说明。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 补齐 status summary 的硬件安全边界：只读 artifact，不打开串口，不发送命令。
- `OKR.md`
  - 保持 O1 约 95.5%，只记录 status 可见性和重启后材料可观测性增强。
- `docs/process/okr_progress_log.md`
  - 追加本轮 O1 micro sprint 进度条目。

## 验证结果

本轮本地验证命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_upper_robot_api.py
```

结果：`Ran 14 tests in 1.150s`，`OK`。

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py
```

结果：exit 0，无输出。

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/o1_upper_robot_api_base_feedback.md docs/interfaces/o7_upper_robot_api.md docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/process/okr_progress_log.md OKR.md sprints/2026.06.03_16-17_o1-feedback-status-summary/tech-done.md
```

结果：exit 0，无输出。

## 远端验证

未执行远端验证，为避免 worker 卡住。本轮没有启动新的 SSH、scp、systemctl 或 curl；也没有调用 `POST /api/base/feedback-samples`、`GET /api/base/feedback-samples/latest`、`GET /api/status`、`/api/base/manual`。

## 剩余风险

- `freshness.status=fresh` 只表示 latest artifact 文件 mtime 在默认 15 分钟窗口内，不证明当前串口在线、robot ACK、HIL pass、`safe_to_control=true` 或真实可运动。
- `latest_t1001_observed_count` 来自历史 artifact，不代表 status 请求本身重新采样。
- 本轮不证明真实 ROS feedback topic、`/odom`、`/imu/data`、`/battery`、真实 `/scan`、manual control、急停演练或完整上车任务。
- 远端 8787 未部署本轮 status summary 改动，仍需后续受控远端部署验证。
