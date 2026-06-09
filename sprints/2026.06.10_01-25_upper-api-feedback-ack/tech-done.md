# Upper API Feedback Ack Tech Done

## sprint_type: micro

## 目标

当前真实上车 capture 已经证明 WAVE ROVER raw UART `T=1001` feedback、ROS2 `/battery`、`/imu/data`、动态 `odom -> base_link` TF、LiDAR、camera、map、route/keyframes 和短程 motion smoke 均可归档。但恢复 `upper_robot_api.py` 后，`/api/base/status.feedback_ack.t1001_observed` 仍显示 `false`，且本地仓库没有 `onboard/scripts/upper_robot_api.py` 源码，导致后续每轮占用 `/dev/ttyS5` 后只能证明 API 进程恢复，不能证明 API 层新鲜底盘反馈恢复。

本轮目标：把上位机实际运行的 `upper_robot_api.py` 纳入仓库治理或补齐等价实现，并修复 `/api/base/status` 对 WAVE ROVER `T=1001` 新鲜 feedback 的识别；结束时在真实上位机归档 `status_before/status_after`，其中至少一次 `feedback_ack.t1001_observed=true`。

## Owner

- 主责：`robot-hardware-engineer`

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

采用的 vendor 事实：WAVE ROVER UART 是 UTF-8 newline-delimited JSON；Orange Pi 当前实测底盘口径为 `/dev/ttyS5 @ 115200`；`T=130` 请求 base feedback，`T=131` 控制 feedback flow，`T=142` 设置反馈间隔，`T=143` 控制 echo，`T=1001` 是 base feedback，字段包含 `L/R/r/p/y/v`。

## 允许改动范围

- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/hardware/wave_rover_json_bridge.md`
- `sprints/2026.06.10_01-25_upper-api-feedback-ack/tech-done.md`
- `sprints/2026.06.10_01-25_upper-api-feedback-ack/artifacts/`

范围外文件不得改动；如发现必须改其他文件，先在输出中说明理由并暂停。

## 功能要求

- 先设计后实现：先读取上位机 `/root/rober/onboard/scripts/upper_robot_api.py`，明确根因和最小修复方案，再改代码。
- 如果本地缺少 `onboard/scripts/upper_robot_api.py`，优先把上位机实际运行版本带回仓库，并在此基础上做最小修复。
- `/api/base/status` 必须能安全执行非运动 readback：发送/使用 vendor feedback 相关命令时不得发送运动命令，不得把 `safe_to_control` 或 `primary_actions_enabled` 误置为 true。
- 解析 `T=1001` 时必须兼容真实板上 `y:"null"`；不能因为 yaw 不可用而丢弃整帧。
- `feedback_ack.t1001_observed=true` 只允许来自本轮新鲜 readback 或新鲜 artifact，不允许由旧 stale artifact 推导。
- 结束必须恢复 `upper_robot_api.py`，并归档恢复后的 `/api/base/status` JSON。
- 文档必须明确 `/api/base/status.feedback_ack` 是非运动 feedback readback，不代表实测里程计或导航级 HIL。

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_upper_robot_api.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/upper_robot_api.py
ssh root@192.168.1.11 -p 37878 'python3 --version && test -e /dev/ttyS5'
ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status'
```

真实上位机复测补充要求：

- 如果需要部署修复版，先备份远端脚本，再同步仓库版本到 `/root/rober/onboard/scripts/upper_robot_api.py`。
- 重启 `upper_robot_api.py` 后，归档：
  - `artifacts/remote_capture/status_before.json`
  - `artifacts/remote_capture/status_after.json`
  - `artifacts/remote_capture/upper_robot_api_restore.log`
  - 必要时归档 `artifacts/remote_capture/feedback_readback.log`
- `status_after.json` 中应出现 `feedback_ack.t1001_observed=true`；若仍为 false，必须定位失败原因并至少重试一次，不得直接收口。

## 实际改动

- 完成时间：2026-06-10 01:30:18 CST。
- 已读资料：
  - `AGENTS.md`
  - `OKR.md`
  - `docs/vendor/VENDOR_INDEX.md`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- 已证实硬件/协议结论：
  - 远端 `/dev/ttyS5` 存在，Python 为 `3.10.12`。
  - 远端 `POST /api/base/feedback-request` 在修复前已能通过非运动 `{"T":130}` 读到 vendor `T=1001`，说明串口和下位机反馈链路可达；证据见 `artifacts/remote_capture/feedback_readback_before_fix.log`。
  - 修复前 `/api/base/status` 的 `feedback_ack.t1001_observed=false` 不是硬件反馈缺失，而是 `base_status()` 硬编码 false 且只读取 stale samples artifact 摘要；证据见 `artifacts/remote_capture/status_before.json`。
  - 修复后 `/api/base/status` 本轮 readback 读到 `observed_feedback_types=[1001]`，`feedback_ack.t1001_observed=true`，来源为 `fresh_readback`；证据见 `artifacts/remote_capture/status_after.json`。
- 文件改动：
  - `onboard/scripts/upper_robot_api.py`
    - 从真实上位机 `/root/rober/onboard/scripts/upper_robot_api.py` 同步实际运行版本进入仓库。
    - 新增 `feedback_type_from_frame()` / `t1001_feedback_observed_in_frame()`，ACK 识别只依赖 vendor `T=1001` 帧身份，兼容 `T` 为数字字符串，且不因 `y:null` 或 `y:"null"` 丢弃整帧。
    - 新增 `feedback_ack_from_fresh_evidence()`，只允许本次 status readback 或 fresh samples artifact 抬高 `feedback_ack.t1001_observed`。
    - `UpperRobotApi.base_status()` 改为执行一次非运动 `T=130` 短窗口 readback，并暴露 `feedback_readback`、`readback_sends_commands`、`sends_motion_commands=false`；`safe_to_control`、`primary_actions_enabled`、`robot_control_executed` 保持 false。
  - `onboard/tests/test_upper_robot_api.py`
    - 新增 unittest 覆盖 `y:"null"`、fresh readback 优先、fresh artifact fallback、`/api/base/status` 安全字段。
  - `docs/hardware/wave_rover_json_bridge.md`
    - 新增 `/api/base/status.feedback_ack` 证据边界：它是非运动 `T=130` readback 或 fresh artifact，不代表 ROS topic 对齐、导航级 HIL 或 safe-to-control。
  - `sprints/2026.06.10_01-25_upper-api-feedback-ack/artifacts/remote_capture/`
    - `status_before.json`
    - `feedback_readback_before_fix.log`
    - `upper_robot_api_backup.log`
    - `upper_robot_api_restore.log`
    - `status_after.json`
- 远端部署：
  - 已备份远端脚本到 `/root/rober/onboard/scripts/upper_robot_api.py.bak_20260610_012916`。
  - 已同步仓库修复版到 `/root/rober/onboard/scripts/upper_robot_api.py`。
  - 第一次重启命令因 zsh 对多行 PID 展开报 `illegal pid`，未形成有效恢复；已改用锚定 `pkill -f '^python3 /root/rober/onboard/scripts/upper_robot_api.py'` 重试成功。
  - 当前远端进程按原参数恢复：`python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`。

## 验证结果

已运行并通过：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_upper_robot_api.py
```

结果：

```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/upper_robot_api.py
```

结果：退出码 0，无输出。

```bash
ssh root@192.168.1.11 -p 37878 'python3 --version && test -e /dev/ttyS5'
```

结果：

```text
Python 3.10.12
```

`test -e /dev/ttyS5` 退出码 0。

```bash
ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status'
```

关键结果（完整 JSON 见 `artifacts/remote_capture/status_after.json`）：

```json
{
  "port": "/dev/ttyS5",
  "baudrate": 115200,
  "feedback_ack": {
    "t1001_observed": true,
    "robot_ack_connected": false,
    "source": "fresh_readback",
    "reason": "T=1001 observed by this /api/base/status non-motion T=130 readback"
  },
  "feedback_readback": {
    "t1001_feedback_status": "observed",
    "observed_feedback_types": [1001],
    "read_line_count": 13,
    "parsed_json_count": 13,
    "invalid_json_count": 0
  },
  "sends_commands": true,
  "sends_motion_commands": false,
  "safe_to_control": false,
  "primary_actions_enabled": false,
  "robot_control_executed": false
}
```

## 剩余风险

- 本轮未发送任何运动命令，也未重新验证轮向、里程计或导航级 HIL；`feedback_ack` 只证明 API 层通过非运动 `T=130` 读到 vendor `T=1001`。
- `/api/base/status` 现在会打开 `/dev/ttyS5` 并发送一次 `T=130`，因此它是只读反馈 readback，不再是纯 stat 接口；文档已同步说明 `sends_commands=true` 但 `sends_motion_commands=false`。
- `robot_ack_connected=false` 仍保持，因为 WAVE ROVER `T=1001` 是 vendor feedback material，不是项目级任务 ACK。
- 远端第一次重启命令失败已定位并重试成功；最终恢复日志和状态均已归档。
