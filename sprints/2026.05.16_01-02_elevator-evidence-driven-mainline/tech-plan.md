# Sprint 2026.05.16_01-02 Elevator Evidence Driven Mainline - Tech Plan

sprint_type: epic

## 1. 新软件证明边界

本轮新增 `software_proof_docker_elevator_evidence_driven_mainline_gate`。它只证明 Docker/local rehearsal evidence artifact、Robot behavior consumption、task record 和 mobile read-only summary 的软件链路可验证。

核心 artifact contract：

- `schema`: `trashbot.elevator_assist_rehearsal_evidence.v1`
- `evidence_boundary`: `software_proof_docker_elevator_evidence_driven_mainline_gate`
- `evidence_ref`: 非空安全字符串，必须能进入 task record。
- `target_floor`: 字符串。
- `delivery_success`: 必须为 `false`。
- `primary_actions_enabled`: 必须为 `false`。
- `same_evidence_ref_required`: 必须为 JSON boolean `true`。
- `phase_evidence`: object，至少覆盖 `waiting_elevator_open`、`entering_elevator`、`requesting_floor_help`、`waiting_target_floor`、`exiting_elevator`。
- `failure`: 可选 object，字段 `phase`、`reason`、`manual_takeover_reason`；存在时 Robot 必须 fail closed。
- `not_proven`: 必须包含 real elevator / HIL / delivery success 等边界。

## 2. 分工与文件范围

### Task A - Autonomy Algorithm Engineer

允许改动：

- `pc-tools/evidence/elevator_assist_rehearsal_evidence.py`
- `pc-tools/evidence/test_elevator_assist_rehearsal_evidence.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/product/elevator_assisted_delivery.md`

实现：

- 新增 CLI，支持 `--output`、`--once-json`、`--evidence-ref`、`--target-floor`、`--failure-phase`。
- 输出并校验 `trashbot.elevator_assist_rehearsal_evidence.v1` artifact。
- 输出 phone-safe summary，不包含 raw ROS topic、serial/UART、WAVE ROVER、local path、credential 或 success phrasing。
- 文档同步说明该 artifact 是 Robot dry-run 主链路输入，不是现场成功证据。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/elevator_assist_rehearsal_evidence.py pc-tools/evidence/test_elevator_assist_rehearsal_evidence.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_elevator_assist_rehearsal_evidence.py
python3 pc-tools/evidence/elevator_assist_rehearsal_evidence.py --help
python3 pc-tools/evidence/elevator_assist_rehearsal_evidence.py --evidence-ref elevator-rehearsal-001 --target-floor 1F --once-json
rg -n "elevator_assist_rehearsal_evidence|software_proof_docker_elevator_evidence_driven_mainline_gate|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md docs/product/elevator_assisted_delivery.md
git diff --check -- pc-tools/evidence/elevator_assist_rehearsal_evidence.py pc-tools/evidence/test_elevator_assist_rehearsal_evidence.py pc-tools/README.md docs/navigation/fixed_route_workflow.md docs/product/elevator_assisted_delivery.md
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `docs/interfaces/ros_contracts.md`

实现：

- 新增参数 `elevator_assist_evidence_file`，仅在 `elevator_assist_mode=dry_run` 时读取。
- 若文件为空或缺失，保持既有 dry-run fallback。
- 若 artifact schema/boundary/boolean/source 字段不满足 contract，fail closed 到 `elevator_failed`，写入 task record。
- 若 artifact 通过，按 `phase_evidence` 驱动 `machine.elevator_phase(...)`，并把 artifact `evidence_ref` 提升到 task record 顶层 `evidence_ref` / `result_path`。
- 固定 `delivery_success=false`、`primary_actions_enabled=false`、`software_proof` source 和 `not_proven`，不触发真实 Nav2/HIL/ACK claim。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
PYTHONDONTWRITEBYTECODE=1 python3 onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
rg -n "elevator_assist_evidence_file|elevator_assist_rehearsal_evidence|software_proof_docker_elevator_evidence_driven_mainline_gate|delivery_success|primary_actions_enabled" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `docs/product/mobile_user_flow.md`

实现：

- `mobile/web` 的 `elevator_assist` panel 兼容并展示 `elevator_assist_rehearsal_evidence` / evidence-driven fields。
- 展示 safe `evidence_ref`、phase evidence、failure/manual takeover、same evidence ref requirement 和 boundary。
- 继续过滤 raw ROS topic、serial/UART、WAVE ROVER、local path、credential、success phrasing。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "elevator_assist_rehearsal_evidence|software_proof_docker_elevator_evidence_driven_mainline_gate|delivery_success|primary_actions_enabled" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json docs/product/mobile_user_flow.md
```

### Task D - Product Manager / OKR Owner

允许改动：

- `sprints/2026.05.16_01-02_elevator-evidence-driven-mainline/tech-done.md`
- `sprints/2026.05.16_01-02_elevator-evidence-driven-mainline/side2side_check.md`
- `sprints/2026.05.16_01-02_elevator-evidence-driven-mainline/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现：

- 工程任务完成后汇总实际改动、验证结果、证据边界和 OKR 影响。
- 只在 O2/O3/O4 软件链路有实际推进时保守更新；O5 不因本轮上调。

验收命令：

```bash
rg -n "elevator_assist_rehearsal_evidence|software_proof_docker_elevator_evidence_driven_mainline_gate|not real|不证明|delivery_success=false|Objective 5" sprints/2026.05.16_01-02_elevator-evidence-driven-mainline OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_01-02_elevator-evidence-driven-mainline OKR.md docs/process/okr_progress_log.md
```

## 3. OKR 最低优先级核对

- 当前最低 Objective：Objective 5，约 66%。
- 本 sprint 是否针对该 Objective：否。
- 理由：本机没有真实硬件，只有 Docker；也没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration。继续本地 O5 metadata 会重复消费 external blocker。
- 本 sprint 选择 Objective 2/3：PR #4/#5 将电梯 assisted delivery 设为 mandatory MVP，最近 13-14 sprint 只完成 execution pack，缺口集中在 same `evidence_ref` 的行为主链路、现场 evidence 消费、task record 和 mobile safe summary。

## 4. 风险与边界

- 本轮不证明真实电梯、真实目标楼层、真实人工协助、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER/UART/HIL、真实手机/browser、真实 dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- 验证只做围栏，禁止新增无关大测试。

