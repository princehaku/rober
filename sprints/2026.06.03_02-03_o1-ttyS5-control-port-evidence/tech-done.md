# O1 ttyS5 Control Port Evidence

## sprint_type

micro

## 本轮目标

复核并留档 2026-06-03 现场底盘串口事实：WAVE ROVER 当前可写控制口是 Orange Pi `/dev/ttyS5 @115200`，不是 USB STC `/dev/ttyACM0`。本轮只做硬件 owner 文档复核和证据分层，不运行任何会导致运动的命令。

## 已读来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`

## 已证实硬件结论

- Vendor 上位机 reference 使用 UART、UTF-8 JSON、每行一个 JSON object，并以 `\n` 结束。
- Vendor Raspberry Pi reference 使用 `/dev/ttyAMA0 @115200`；Orange Pi 真实串口路径必须现场确认，不能照抄 Raspberry Pi 路径。
- `T=1` 是 vendor `CMD_SPEED_CTRL` 左右轮速度命令。
- `T=130` 是 vendor `CMD_BASE_FEEDBACK`，预期 base feedback 类型为 `T=1001`。
- 现场事实显示 `/dev/ttyS5 @115200` 上 `T=1,L=0.08,R=0.08` 可让底盘响应，随后现场执行 `T=1,L=0,R=0` 停车。
- `/dev/ttyACM0` 仍按前序材料归类为 STC/LiDAR 风险口，不能作为 WAVE ROVER 控制口证据。
- `/dev/ttyS5` 上仍未读到 `T=1001`，反馈/ACK/HIL 未闭环。

## 实际改动

- `docs/interfaces/o7_realtime_hardware_sources.md`：补充 Hardware owner 复核口径、vendor 源码证据、`ttyS5` 证据边界和短时点动/急停门槛。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`：新增 2026-06-03 `/dev/ttyS5` 控制口证据分层、不能外推项和下一步 HIL 门槛。
- `docs/interfaces/o1_o5_90_evidence_boundary.md`：补充 `ttyS5_control_port_observed_not_hil` 边界，明确仍不满足 O1 HIL packet 条件。
- `OKR.md`：把 O1 当前口径更新为 `ttyS5 control write observed + low-speed T=1 field response observed; T=1001/ACK/HIL not_proven`，但因 `T=1001/ACK/HIL` 仍未证明，Product closeout 保持约 93%。
- `docs/process/okr_progress_log.md`：新增本轮 Micro closeout 记录。
- `sprints/2026.06.03_02-03_o1-ttyS5-control-port-evidence/tech-done.md`：新增本文件。

## 验证结果

本轮必须验证命令：

```bash
sed -n '1,220p' docs/vendor/VENDOR_INDEX.md
```

结果：exit 0。关键事实包括 WAVE ROVER 上下位机链路为 UART、newline-delimited JSON；vendor Raspberry Pi 默认 `/dev/ttyAMA0 @115200` 或 `/dev/serial0 @115200`；Orange Pi 真实 UART 设备必须现场确认；`T=1`、`T=130`、`T=131`、`T=142`、`T=143` 均在索引中列明。

```bash
rg -n "115200|ttyAMA0|serial0|write\(|json.dumps|base_speed_ctrl|base_json_ctrl|readline|decode|T.*130|T.*1" docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
```

结果：exit 0。关键片段：`self.ser.write((json.dumps(data) + '\n').encode("utf-8"))`、`base_speed_ctrl()` 构造 `{"T":1,"L":input_left,"R":input_right}`、reference 入口 `BaseController('/dev/ttyAMA0', 115200)`，备用注释 `/dev/serial0, 115200`。

```bash
rg -n "CMD_SPEED_CTRL|CMD_BASE_FEEDBACK|FEEDBACK_BASE_INFO|1001|case 1|case 130|Serial|println|serializeJson|readStringUntil|deserializeJson|115200" docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h
```

结果：exit 0。关键片段：`FEEDBACK_BASE_INFO 1001`、`CMD_SPEED_CTRL 1`、`CMD_BASE_FEEDBACK 130`、`Serial.begin(115200)`、`uart_ctrl.h` 接收串口字符并在 newline 后 `deserializeJson()`、`ugv_advance.h` 中 `baseInfoFeedback()` 序列化并 `Serial.println()`。

```bash
git diff --check -- docs/interfaces/o7_realtime_hardware_sources.md docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_o5_90_evidence_boundary.md OKR.md docs/process/okr_progress_log.md sprints/2026.06.03_02-03_o1-ttyS5-control-port-evidence/tech-done.md
```

结果：exit 0，无 trailing whitespace 或 conflict marker。

## 安全声明

- 本轮未发送任何运动命令。
- 本轮未打开或写入任何串口。
- 本轮未 SSH 到上位机。
- 本轮未观察到或证明 `T=1001`。

## 剩余风险

- `T=1001` feedback/ACK 未读到，`/odom`、`/imu/data`、`/battery` 仍无实车同源材料。
- 自动停车、急停、速度限幅、操作日志和 PC/ROS 控制入口 fail-closed 尚未实现和验证。
- `/dev/ttyS5` 的 wiring、权限、串口占用和长期稳定性需要真实上车 HIL 再确认。
- 下一步短时点动必须先满足 operator、低速、短时、自动停车和人工断电/急停门槛。

## Product Closeout

- OKR 映射：Objective 1。
- 方向判断：继续。
- 进度口径：保持约 93%，理由是 `/dev/ttyS5 @115200` 已有 CEO 现场 control write observed 和低速 `T=1` 响应事实，但 `T=1001/ACK/HIL` 仍未证明，不能提升为 HIL 或闭环控制完成。
- 验收边界：该证据只证明 `ttyS5 control write observed`，不证明 `T=1001` feedback、robot ACK、HIL packet、真实 `/imu/data`、`/battery`、`/odom`、ROS `/cmd_vel` 接入、自动停车/急停产品化或 delivery success。
- 下一轮优先级：围绕 `/dev/ttyS5` 做短时点动安全门槛、自动停车、速度/时长参数化、operator 日志、人工急停和 `T=1001`/ACK 采集。
