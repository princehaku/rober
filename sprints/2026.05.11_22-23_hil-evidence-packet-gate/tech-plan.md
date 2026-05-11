# Sprint 2026.05.11_22-23 HIL Evidence Packet Gate - Tech Plan

## 状态

- 阶段：tech-plan
- 时间：2026-05-11 22:00 Asia/Shanghai
- 主责 owner：`hardware-engineer`
- 协作方式：`hardware-engineer` 单线闭环实现；`robot-software-engineer` 和 `autonomy-engineer` 只在 `evidence_ref` 对接事实不清时做只读咨询。

## 目标

实现一个 Docker-only 可运行的 HIL evidence packet gate，让真实上车前/上车后证据包可以被脚本严格预检，并明确判定：

1. `software_proof`：脚本、格式或 dry-run 证据合规，但不代表真实硬件通过。
2. `blocked`：缺真实串口、缺必需文件、缺反馈帧、缺 ROS topic sample、Docker/Humble preflight 阻塞或 packet 字段不完整。
3. `hil_pass`：真实 WAVE ROVER run 的 packet 满足必需文件、反馈、topic sample、同一 `evidence_ref` 和来源字段要求。

本轮计划不得要求在当前无硬件机器上产生 `hil_pass`。

## 事实来源和近期证据

- `OKR.md` 4.1：O1 约 75%，低于 O2/O3/O4/O5；O1 仍缺真实 WAVE ROVER `hil_pass` evidence packet。
- `sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/final.md`：Docker/Humble preflight 已归因为 registry mirror/proxy，且本机无真实串口，不能产生 `hil_pass`。
- `sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/tech-done.md`：required evidence files 包括 `command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`，且 `--status` 只是 `software_proof`。
- `sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/final.md`：O2/O3 software proof 已可按同一 `evidence_ref` 复账，但仍需真实 HIL/route run 后交叉 proof。
- CEO 约束：本机没有真实硬件，只有 Docker；要功能往前走；测试只围栏；优先推进 OKR 完成度低的部分；最后提交并推送。

## 实现阶段文件范围

建议允许 `hardware-engineer` 修改：

- `scripts/hardware_smoke_wave_rover.py`（若现有 smoke 脚本最适合承载 gate）
- `scripts/hil_evidence_packet_gate.py`（若拆成独立 gate 更清晰）
- `docs/acceptance/wave_rover_hil_evidence.md`
- `docs/acceptance/hil_runbook.md`
- `docs/acceptance/robot_bringup_checklist.md`
- `sprints/2026.05.11_22-23_hil-evidence-packet-gate/tech-done.md`
- 必要时创建最小 fixture 目录，用于 blocked/software proof packet 围栏验证

禁止触碰：

- `.codex/config.toml`
- 与 O1 evidence gate 无关的 README、UI、Nav2、行为状态机功能
- 无关硬件配置、launch 参数或 vendor 文件
- 宽泛测试矩阵和大范围重构

## 任务拆解

### Task 1：定义 packet gate contract

Owner：`hardware-engineer`

工作内容：

- 明确 gate 输入为 evidence run 目录，目录内至少需要检查：
  - `command.txt`
  - `serial.log`
  - `feedback_T1001.log`
  - `odom_once.jsonl`
  - `imu_once.jsonl`
  - `battery_once.jsonl`
- 明确每个 packet 必须有可追踪 `evidence_ref`。
- 明确 `source` 只能归入 `software_proof`、`blocked`、`hil_pass`；如果历史字段出现 `simulated` 或脚本名来源，必须降级为非 `hil_pass`。
- 明确缺文件、空文件、无 `T=1001`、无 topic sample、无真实串口来源都不得通过 `hil_pass`。

验收命令建议：

```bash
python3 scripts/hil_evidence_packet_gate.py --help
```

预期：输出 gate 用法，不要求真实硬件。

### Task 2：实现 Docker-only blocked/software proof fixture

Owner：`hardware-engineer`

工作内容：

- 准备最小 evidence fixture 或临时目录，模拟当前 Docker-only/无串口状态。
- gate 应返回 `blocked` 或 `software_proof`，并输出明确缺口，例如 missing serial device、missing packet file、missing topic sample。
- `hardware_smoke_wave_rover.py --status` 的输出不得被 gate 提升为 `hil_pass`。

验收命令建议：

```bash
python3 scripts/hardware_smoke_wave_rover.py --status
python3 scripts/hil_evidence_packet_gate.py --packet-dir <blocked_or_fixture_packet_dir>
```

预期：`--status` 为 readiness/software proof；gate 对 blocked fixture 不通过 `hil_pass`。

### Task 3：实现 `hil_pass` 严格门槛

Owner：`hardware-engineer`

工作内容：

- 对 `feedback_T1001.log` 检查至少存在真实 `T=1001` 反馈片段。
- 对 `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 检查非空且能解析为 JSON line。
- 对 `command.txt` 检查包含本次 move-test 命令或 evidence run 入口命令。
- 对 `serial.log` 检查不能只是 serial open failure；若记录无真实串口或 no such file/device，必须判定为 `blocked`。
- 输出包含 packet 判定、失败项列表、`evidence_ref`、`source` 和 `blocked_reason`。

验收命令建议：

```bash
python3 -m py_compile scripts/hil_evidence_packet_gate.py
python3 scripts/hil_evidence_packet_gate.py --packet-dir <fixture_packet_dir>
```

预期：fixture 只能通过其真实类别，不允许 blocked fixture 通过 `hil_pass`。

### Task 4：保留 O2/O3 crosscheck 接口

Owner：`hardware-engineer`

咨询：`robot-software-engineer`、`autonomy-engineer`

工作内容：

- gate 输出或 packet metadata 必须保留同一 `evidence_ref`。
- 文档写清后续真实 route/task record 可通过 `scripts/evidence_crosscheck.py` 与该 `evidence_ref` 复账。
- 不在本轮实现 O2/O3 新逻辑，不改 task orchestrator 或 fixed-route 行为。

验收命令建议：

```bash
python3 -m py_compile scripts/evidence_crosscheck.py
```

预期：不破坏现有 crosscheck 脚本；如未修改该脚本，命令可作为围栏。

### Task 5：Sprint 执行记录和收口

Owner：`hardware-engineer`

工作内容：

- 更新 `tech-done.md`，记录实际改动、gate 输出、验证结果、失败定位和剩余风险。
- 如 gate 完成但本机仍无硬件，结论写为 Docker-only gate ready，real `hil_pass` pending。
- 如 Docker/Humble 或环境阻塞影响实现，写清 blocked 原因，不能暗示已产生 HIL evidence。

验收命令建议：

```bash
git diff --check -- <touched files>
```

注意：只检查 touched files，避免无关 README whitespace 干扰。

## 接口影响

- 不改变 ROS2 package API。
- 不改变 WAVE ROVER UART JSON 协议语义。
- 不改变 O2/O3 task record、route replay、operator UI contract。
- 新增或增强的 gate 只负责 evidence packet 合规检查，不负责真实驱动底盘。

## 本轮文档验收命令

本轮 Product 文档必须运行：

```bash
test -f sprints/2026.05.11_22-23_hil-evidence-packet-gate/pre_start.md && test -f sprints/2026.05.11_22-23_hil-evidence-packet-gate/prd.md && test -f sprints/2026.05.11_22-23_hil-evidence-packet-gate/tech-plan.md
git diff --check -- sprints/2026.05.11_22-23_hil-evidence-packet-gate/pre_start.md sprints/2026.05.11_22-23_hil-evidence-packet-gate/prd.md sprints/2026.05.11_22-23_hil-evidence-packet-gate/tech-plan.md
```

## 实现阶段围栏命令

实现 owner 必须按实际文件范围运行最小围栏：

```bash
python3 -m py_compile scripts/hil_evidence_packet_gate.py
python3 scripts/hardware_smoke_wave_rover.py --status
python3 scripts/hil_evidence_packet_gate.py --packet-dir <blocked_or_fixture_packet_dir>
git diff --check -- <touched files>
```

如果 gate 复用 `scripts/hardware_smoke_wave_rover.py` 而不新增 `scripts/hil_evidence_packet_gate.py`，则把 py_compile 和 CLI 命令替换为实际脚本入口，并在 `tech-done.md` 写清原因。

## 风险边界

- 当前机器无真实串口，不能完成 `hil_pass`。
- Docker registry mirror/proxy 仍可能阻塞完整 Humble build；gate 应尽量保持普通 Python/文件层可验证。
- 空文件、blocked log、serial open failure、缺 `T=1001`、缺 topic sample 都必须失败或 blocked，不能通过 `hil_pass`。
- O2/O3 same-`evidence_ref` 交叉 proof 仍等待真实 HIL packet 与 route/task record 实跑样本。

## 完成前反思清单

- 是否仍以 O1 为主线，没有漂移到 UI 或宽泛路线功能？
- 是否明确区分 `software_proof`、`blocked`、`hil_pass`？
- 是否没有在无硬件机器上声明真实 HIL 通过？
- 是否只改允许文件，且未触碰 `.codex/config.toml`？
- 是否运行了围栏命令，或记录了无法运行的具体原因？
- 是否把实现结果写入 `tech-done.md`，并在需要时更新 `side2side_check.md` / `final.md`？
