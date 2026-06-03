# O1 8787 T130 Feedback Endpoint Micro Sprint

## sprint_type: micro

Owner: Hardware Infra Engineer

目标：在 8787 统一上位机 API 中新增显式、非运动的 `POST /api/base/feedback-request`，让 O1 从离线 probe 才能采反馈，推进到统一 API 可采 `T=130 -> T=1001` 材料。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/battery_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `POST /api/base/feedback-request`。
  - 只发送一次 vendor `{"T":130}`，随后短窗口读取 newline-delimited JSON。
  - 输出 `serial_open`、`serial_write`、`serial_read`、`read_line_count`、`parsed_json_count`、`invalid_json_count`、`observed_feedback_types`、`t1001_feedback_status`、`feedback_ack`、`blocked_commands_not_sent` 和 `vendor_sources`。
  - 固定 `safe_to_control=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。
- `onboard/scripts/test_upper_robot_api.py`
  - fake serial 增加 `readline()` 预置反馈能力。
  - 覆盖 status 不触发串口、feedback request 只写 `T=130`、解析 `T=1001`、坏 JSON 计数、写失败 fail-closed。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 增加 8787 显式 `T=130` feedback endpoint 边界说明。
- `docs/interfaces/o1_upper_robot_api_base_feedback.md`
  - 新增接口 contract。
- `OKR.md`
  - 保守补充 8787 显式 `T=130` feedback request endpoint ready / fake serial contract passed；O1 仍约 94%，真实 `T=1001`、ACK、HIL 和 `safe_to_control` 仍 `not_proven`。
- `docs/process/okr_progress_log.md`
  - 追加本 micro sprint 的 O1 进度记录，明确 fake serial/API contract 通过和真实材料缺口。

## 验证结果

已按硬截止只运行三条验收命令，全部通过：

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

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_upper_robot_api_base_feedback.md docs/process/okr_progress_log.md OKR.md sprints/2026.06.03_11-12_o1-8787-t130-feedback-endpoint/tech-done.md
```

输出片段：无输出，exit 0。

测试使用 fake serial，不打开真实硬件，不 POST `/api/base/manual`。

## 剩余风险

- 本轮没有访问真实 `/dev/ttyS5`，没有 SSH，上位机 8787 未现场复跑。
- fake serial 只能证明 API 合同和解析逻辑，不能证明真实 WAVE ROVER 会返回 `T=1001`。
- 即使后续该 endpoint 观察到 `T=1001`，仍需同源 HIL packet、至少两帧真实反馈、ROS `/odom`、`/imu/data`、`/battery` 和 operator report 才能推进 HIL pass。
