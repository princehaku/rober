# Sprint 2026.05.16_19-20 Route Task Terminal Review Decision - Tech Plan

sprint_type: epic

## 1. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5。
3. 理由：Objective 5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。本机只有 Docker，继续新增 O5 local metadata 只能重复 blocked-by-design artifact，不能构成 external proof。
4. Objective 1 约 75%，是下一低 Objective；但最近两轮 `2026.05.16_17-18_hardware-baseline-source-alignment` 和 `2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck` 已连续消费 PR #5 的硬件基线 / source / precheck blocker。本机无真实硬件，不应第三轮继续堆同类 hardware gate。
5. 本 sprint 改攻 Objective 2 / Objective 3 的可行动作：`route_task_terminal_review_decision`，把上一轮 `route_task_terminal_completion_rehearsal` software-proof 摘要转为 operator review decision、owner handoff、next-required-evidence 和 field retest request guidance。

## 2. 证据依据

- `OKR.md` 4.1：Objective 5 约 66% 最低，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；Docker-only 本地 metadata 不提升 O5。
- `OKR.md` 4.1：Objective 1 约 75%，但仍缺真实 WAVE ROVER `hil_pass`、真实串口日志、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本和真实 2D LiDAR / ToF 材料。
- PR #5 review：默认硬件集与强制传感器基线矛盾；OKR 最低目标叙述漂移；强制传感器假设缺 `docs/vendor` 来源。
- `sprints/2026.05.16_17-18_hardware-baseline-source-alignment/final.md`：PR #5 硬件基线/source 风险已被转成 `software_proof_docker_hardware_baseline_source_alignment_gate`，但没有真实 WAVE ROVER/UART/HIL 或真实传感器材料。
- `sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/final.md`：PR #5 参数化 config precheck 风险已被转成 `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`，但仍不是真实硬件、真实手机/browser、真实 HIL、真实送达或 Objective 5 external proof。
- `sprints/2026.05.16_16-17_route-task-terminal-completion-rehearsal/final.md`：已有 `software_proof_docker_route_task_terminal_completion_rehearsal_gate`，但仍缺真实 Nav2/fixed-route runtime log、task record、route completion signal、门状态、楼层确认、人工协助记录、dropoff/cancel completion 或 delivery result。

## 3. 统一接口

- Artifact schema：`trashbot.route_task_terminal_review_decision.v1`
- Summary schema：`trashbot.route_task_terminal_review_decision_summary.v1`
- 输入来源：`trashbot.route_task_terminal_completion_rehearsal.v1` 或 `trashbot.route_task_terminal_completion_rehearsal_summary.v1`
- Evidence boundary：`software_proof_docker_route_task_terminal_review_decision_gate`
- 缺失默认状态：`blocked_missing_route_task_terminal_review_decision`
- 固定边界：`software_proof` only、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

## 4. 并行 owner 任务

### Task A：Autonomy Review Decision Gate

责任 Engineer：Autonomy Algorithm Engineer。

允许改动：

- `pc-tools/evidence/route_task_terminal_review_decision.py`
- `pc-tools/evidence/test_route_task_terminal_review_decision.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 新增 dependency-free CLI，读取 `route_task_terminal_completion_rehearsal` artifact / summary。
- 输出 review decision artifact / summary，schema 与 boundary 使用本 plan 第 3 节。
- 输出字段至少包含 `review_decision`、`decision_reason`、`owner_handoff`、`next_required_evidence`、`field_retest_request_guidance`、safe `evidence_ref`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Fail closed：缺输入、bad JSON、unsupported schema/boundary、same `evidence_ref` mismatch、unsafe copy、`delivery_success=true`、`primary_actions_enabled=true`、raw path/credential/ROS topic/serial/WAVE ROVER/HIL/success wording。
- 新增代码技术注释必须使用中文，解释为什么 review decision 只能把材料转为复测指导，不能证明送达。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_terminal_review_decision.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_terminal_review_decision.py
python3 pc-tools/evidence/route_task_terminal_review_decision.py --help
rg -n "route_task_terminal_review_decision|software_proof_docker_route_task_terminal_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|field retest|owner_handoff|next_required_evidence" pc-tools docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_terminal_review_decision.py pc-tools/evidence/test_route_task_terminal_review_decision.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B：Robot Diagnostics Metadata-only Consumer

责任 Engineer：Robot Platform Engineer。

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 支持从 explicit ref/env/status/diagnostics nested source 读取 `route_task_terminal_review_decision` 或 summary。
- metadata-only 输出 review decision、safe `evidence_ref`、owner handoff、next-required-evidence、field retest request guidance。
- 缺失/unsupported/unsafe/same evidence_ref mismatch 均 fail closed 为 `blocked_missing_route_task_terminal_review_decision` 或相应 unsafe status。
- 不触发 `/api/collect`、dropoff、cancel、ACK、cursor advance、terminal ACK、Nav2、WAVE ROVER、HIL、production readiness、dropoff/cancel completion 或 delivery success。
- 新增代码技术注释必须使用中文，解释为什么 diagnostics 只能显示证据决策，不能授权控制。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_terminal_review_decision|software_proof_docker_route_task_terminal_review_decision_gate|blocked_missing_route_task_terminal_review_decision|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C：Full-stack Review Decision Panel

责任 Engineer：User Touchpoint Full-Stack Engineer。

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现要求：

- 在 route/elevator、completion signal、terminal completion rehearsal 附近新增只读“终态复核决策” panel。
- 消费 `route_task_terminal_review_decision`、`route_task_terminal_review_decision_summary`、`phone_readiness`、`/api/diagnostics`、nested diagnostics summary 中兼容字段。
- 展示 review decision、decision reason、safe `evidence_ref`、owner handoff、next-required-evidence、field retest request guidance、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- copy/export whitelist-only，不展示 raw JSON、ROS topic、串口、凭证、完整本机路径、checksum、完整 artifact、HIL 或成功送达文案。
- Start / Confirm Dropoff / Cancel gating 不变。
- 新增代码技术注释必须使用中文，解释为什么该 panel 只读且不授权控制。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "route_task_terminal_review_decision|终态复核决策|software_proof_docker_route_task_terminal_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

### Task D：Product Closeout

责任 Engineer：Product Manager / OKR Owner。

允许改动：

- `sprints/2026.05.16_19-20_route-task-terminal-review-decision/tech-done.md`
- `sprints/2026.05.16_19-20_route-task-terminal-review-decision/side2side_check.md`
- `sprints/2026.05.16_19-20_route-task-terminal-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 汇总 Autonomy / Robot / Full-stack worker 的实际改动、验证命令、失败定位和剩余风险。
- 回顾本轮是否仍符合 OKR 最低优先级核对：Objective 5 仍最低但外部阻塞；Objective 1 已连续两轮消费 PR #5 硬件 blocker 且缺真实硬件；本轮只提升 Objective 2 / Objective 3 的 software-proof 准备度。
- `OKR.md` 只允许按 software proof 保守更新；没有真实材料时，不提升 Objective 1 / Objective 5，不声明真实 completion、HIL 或 delivery success。
- closeout 必须明确本轮不证明真实 Nav2/fixed-route、真实 route/elevator field pass、真实 dropoff/cancel completion、delivery success、真实手机/browser、WAVE ROVER/UART/HIL 或 Objective 5 external proof。

验收命令：

```bash
rg -n "route_task_terminal_review_decision|software_proof_docker_route_task_terminal_review_decision_gate|Objective 5|Objective 1|Objective 2|Objective 3|PR #5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_19-20_route-task-terminal-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_19-20_route-task-terminal-review-decision OKR.md docs/process/okr_progress_log.md
```

## 5. 接口影响

- 新增 PC evidence artifact / summary schema；只读、dependency-free、Docker/local。
- Robot diagnostics 新增 metadata-only consumer；不触发控制链路。
- Mobile/web 新增只读 panel；主操作按钮授权条件不变。
- 不新增硬件、UART、launch 参数、ROS action/topic/service 运行时契约。

## 6. 风险边界

- 本轮不是真实 dropoff/cancel completion 或 delivery success。
- 本轮不是真实 route/elevator field pass、Nav2/fixed-route runtime proof、真实路线采集、真实电梯、真实手机/browser、production app、WAVE ROVER/UART/HIL 或 Objective 5 external proof。
- 若 worker 发现 terminal completion rehearsal 已覆盖部分字段，仍应把本轮增量控制在 review decision / owner handoff / field retest guidance，不做无关重构。

## 7. Sprint 文档要求

- Planning 阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后补齐：`tech-done.md`、`side2side_check.md`、`final.md`。
- 不允许一次性预生成 closeout 文档；closeout 必须基于 worker 实际验证结果。

## 8. 本轮 planning 验收命令

```bash
rg -n "route_task_terminal_review_decision|Objective 5|Objective 1|Objective 2|Objective 3|PR #5|Docker|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_19-20_route-task-terminal-review-decision
git diff --check -- sprints/2026.05.16_19-20_route-task-terminal-review-decision/pre_start.md sprints/2026.05.16_19-20_route-task-terminal-review-decision/prd.md sprints/2026.05.16_19-20_route-task-terminal-review-decision/tech-plan.md
```
