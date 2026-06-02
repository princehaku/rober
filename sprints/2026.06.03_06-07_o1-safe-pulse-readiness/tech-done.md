# 2026.06.03_06-07 O1 Safe Pulse Readiness Remote Read-only Check

## sprint_type

micro

## Owner

robot-hardware-engineer

## 实际改动

- 新增本轮 micro sprint 留档 `sprints/2026.06.03_06-07_o1-safe-pulse-readiness/tech-done.md`。
- 更新 `OKR.md` 的 O1 当前事实：补充 2026-06-03 06-07 远端 8787 只读确认和 dry-run artifact，不上调 O1 百分比。
- 更新 `docs/interfaces/o1_o5_90_evidence_boundary.md`：补充远端 8787 read-only status + O1 runner dry-run 不提升 90% / HIL 的边界。
- 更新 `docs/process/okr_progress_log.md`：追加本轮 O1 hourly iteration 事实。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/interfaces/o7_upper_robot_api.md`
- `docs/interfaces/o1_o5_90_evidence_boundary.md`

## 已证实的硬件结论

- WAVE ROVER vendor 资料确认底盘上位机链路是 UART newline-delimited UTF-8 JSON；`T=1` 是左右轮速度命令，`T=13` 是 ROS velocity 命令，`T=130` 请求 base feedback，`T=131` 控制 feedback flow，`FEEDBACK_BASE_INFO=1001` 是 base feedback 类型。
- vendor Raspberry Pi reference 默认 `/dev/ttyAMA0 @115200` 不能直接当 Orange Pi 结论；本轮远端 8787 status 只读确认当前上位机 base 配置是 `/dev/ttyS5 @115200`。
- 远端 `trashbot-upper-robot-api.service` 已 `enabled/active/running`，8787 正在监听，进程参数包含 `--base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`。
- 远端 `GET /api/status` 返回 camera ready、radar `/dev/ttyACM0` STC/LiDAR 风险口、base `/dev/ttyS5 @115200`、`write_control_available=true`、`t1001_observed=false`、`robot_ack_connected=false`。
- 本轮没有发送任何运动命令，没有 POST `/api/base/manual` 或 `/api/base/stop`，没有打开串口，没有发送 `T=1/T=13/T=130/T=131`，没有发送 ROS `/cmd_vel`。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/upper_robot_api.py
```

结果：exit 0，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_upper_robot_api.py
```

结果：

```text
..........
----------------------------------------------------------------------
Ran 10 tests in 0.864s

OK
```

远端只读状态命令：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=6 -p 37878 root@192.168.1.11 'ss/systemctl/curl GET only'
```

关键输出：

```text
LISTEN 0 128 0.0.0.0:8787 ... users:(("python3",pid=25470,fd=6))
trashbot-upper-robot-api.service - Trashbot unified upper robot API
Loaded: loaded (/etc/systemd/system/trashbot-upper-robot-api.service; enabled)
Active: active (running) since Wed 2026-06-03 03:38:45 CST
ExecStart=/usr/bin/env bash /root/rober/onboard/scripts/upper_robot_api.sh
```

`GET /api/status` 关键字段：

```json
{
  "camera": {"http_status": 200, "status": "ready", "video_source": "auto"},
  "radar": {"scan_status": "not_proven", "observed_lidar_port": "/dev/ttyACM0", "baudrate": 150000},
  "base": {
    "port": "/dev/ttyS5",
    "baudrate": 115200,
    "write_control_available": true,
    "feedback_ack": {
      "t1001_observed": false,
      "robot_ack_connected": false,
      "reason": "T=130 on /dev/ttyS5 did not return T=1001 in current evidence"
    },
    "sends_commands": false,
    "safe_to_control": false,
    "robot_control_executed": false
  }
}
```

本地 runner 对远端 8787 dry-run：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py \
  --base-url http://192.168.1.11:8787 \
  --dry-run \
  --once-json \
  --output /tmp/rober_o1_artifacts/o1_safe_pulse_dry_run_2026-06-03T0511.json
```

artifact 关键字段：

```json
{
  "schema": "trashbot.o1.ttyS5_safe_pulse_acceptance.v1",
  "evidence_boundary": "api_status_dry_run_not_hil",
  "execution_gate": {
    "authorized": false,
    "dry_run": true,
    "execute_motion": false,
    "confirm_physical_clearance": false
  },
  "manual_request": null,
  "stop_request": null,
  "sends_commands": false,
  "sends_motion_commands": false,
  "robot_control_executed": false,
  "safe_to_control": false,
  "t1001_feedback_status": "not_observed",
  "blocked_commands_not_sent": [
    {"command": {"T": 1}},
    {"command": {"T": 13}},
    {"command": {"T": 130}},
    {"command": {"T": 131}},
    {"command": "cmd_vel"}
  ]
}
```

`git diff --check` 在本轮允许范围内执行，结果 exit 0，无输出。

## 是否发送运动命令

否。本轮远端命令仅包含 `ss`、`systemctl status/cat`、`ps`、`curl GET /api/status`、`curl GET /api/base/status`；本地 runner 使用 `--dry-run`，只 GET status。没有 POST `/api/base/manual`，没有 POST `/api/base/stop`，没有串口写入，没有 ROS `/cmd_vel`。

## 失败定位

- 无服务恢复失败：8787 服务已运行，未执行 `install_upper_robot_api_service.sh`。
- 未在远端直接运行 runner：候选路径探测未找到本轮 runner 文件可执行路径，因此改为本地 runner 通过远端 8787 HTTP GET dry-run 采集 artifact；该路径仍满足只读、不运动边界。

## 剩余风险

- BLOCKED_ON_PHYSICAL_CLEARANCE：没有现场看护、物理净空、人工急停确认，本轮不执行真实 pulse。
- `T=1001`、robot ACK、真实 `/odom`、`/imu/data`、`/battery`、自动停车真实演练、急停路径和 HIL packet 仍为 `not_proven`。
- 本轮只证明 8787 服务在线、状态面可读、dry-run 默认不运动；不能写成 HIL pass、闭环安全控制、真实 `/cmd_vel` 接入或 delivery success。
- Micro sprint 软提醒：本轮直接针对当前最低 Objective O1。

## Product closeout / OKR verdict

用户价值和北极星：本轮把 O1 从“runner ready / watched execution pending”继续压实到“远端 8787 服务在线 + 状态面可读 + safe pulse runner dry-run artifact 可采集”。这对普通用户价值的真实贡献是降低下一次现场点动的误操作风险，并让底盘控制证据能被后续 PC/ROS 链路复用；不是证明机器人已经能安全运动或送达。

OKR 映射和方向判断：Objective 1 继续推进，方向为 `safe pulse readiness -> watched field pulse execution`。本轮不切换到 O5/O6/O7，因为 O1 是当前最低 Objective，且仍有非运动真实材料可采。无人 SSH 自动运动命令保持暂停；只有现场看护、物理净空和人工急停明确满足后，Hardware Infra 才能进入真实短 pulse。

KR 拆解和历史归档：O1 KR3 的 ACK/`T=1001`、真实 `/odom`、`/imu/data`、`/battery` 仍未完成；KR4/安全护栏获得远端 8787 read-only status 与 dry-run artifact 支撑。没有 KR 进入历史归档区，历史记录位置为本文件和 `docs/process/okr_progress_log.md` 的 `2026-06-03 06-07｜O1 safe pulse readiness boundary` 小节。

验收口径：可以计入 O1 readiness 的证据是 8787 active/listening、`GET /api/status` 可解析、base 指向 `/dev/ttyS5 @115200`、runner dry-run artifact 明确 `sends_motion_commands=false`、`robot_control_executed=false`、`safe_to_control=false`、`t1001_feedback_status=not_observed`。不能提高 O1 百分比的材料是 SSH 可达、8787 listening、status 200、runner dry-run、PC 面板展示或 camera/radar 状态。O1 上调的最低门槛仍是现场看护 + 物理净空 + 人工急停 + 8787 低速短 pulse + stop 复位 + ACK 或 `T=1001` 同源证据。

OKR 进度建议：O1 保持约 93%；O5 保持约 96%；O6 保持约 96%；O7 保持约 98%。理由是本轮没有真实 watched pulse、没有 ACK、没有 `T=1001`，也没有真实 ROS topic 或 delivery success。`OKR.md` 当前百分比不应上调。
