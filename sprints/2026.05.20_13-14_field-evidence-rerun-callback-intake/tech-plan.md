# Sprint 2026.05.20_13-14 Field Evidence Rerun Callback Intake - Tech Plan

## 1. 目标

实现 `field_evidence_rerun_callback_intake`：只读接收上一轮 `field_evidence_rerun_material_dispatch` 派发后现场 owner 返回的 callback packet，校验真实材料是否按 requirement 回填，并输出 accepted / missing / rejected / blocked 的 intake summary。

本轮固定证据边界：

- `software_proof_docker_field_evidence_rerun_callback_intake_gate`

固定安全状态：

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮不提升 OKR 百分比，除非真实材料实际出现并可由 Product closeout 复核。当前计划按 Docker-only software-proof 边界执行。

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对理由：Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；本机只有 Docker，继续堆同义 O5 local metadata 会重复消费同一 blocker。
4. 当前下一低项 Objective 1 约 81%。本 sprint 不直接提高 Objective 1，因为 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；GitHub review thread evidence shows Q/U resolved, X unresolved，latest manual reply `3269642220` 仍不是真实硬件 proof。
5. Objective 4 约 99%，仍缺真实手机/browser、production app、PWA prompt/userChoice 和真实 route/elevator field pass；本轮 mobile/web 只读 panel 不能写成 Objective 4 实机验收。
6. 本 sprint 选择 O2/O3/O4 的 field evidence rerun callback intake，是因为上一轮已 dispatch 真实材料要求，本轮要接收和校验现场 owner callback packet，而不是重复 dispatch。

## 3. Repeated Blocker Rationale

O5 外部 proof blocker 已被多轮识别：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof 不在 Docker-only 主机内。继续做 cloud local metadata 不会改变 Objective 5 约 68% 的主要缺口。

O1 / PR #5 blocker 也仍在真实硬件材料：`PRRT_kwDOSWB9286CJ3tX` 需要真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 或真实 WAVE ROVER/UART/HIL evidence。Q/U resolved 和 manual reply `3269642220` 不足以关闭 X。

上一轮 `field_evidence_rerun_material_dispatch` 已把 O2/O3/O4 的真实材料要求转成 owner work orders、rerun commands 和 callback packet requirements。从第 2 轮开始继续推进同一链路的正确动作是 intake callback packet，而不是重复派发。

## 4. 并行 Owner / File Scope

本轮是 Epic sprint。实现阶段必须并行启动 3 个 Engineer worker，Product 后置 closeout。Autonomy、Robot、Full-stack 文件范围互不重叠；Product 只在 engineer 完成后收口文档、OKR 和 progress log。

### Task A - Autonomy Algorithm Engineer

允许改动：

- `pc-tools/evidence/field_evidence_rerun_callback_intake.py`
- `tests/test_field_evidence_rerun_callback_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md` 或现有 evidence contract doc

实现要求：

- 只读消费上一轮 `field_evidence_rerun_material_dispatch` summary / artifact，以及现场 owner 返回的 callback packet。
- 输出 artifact schema `trashbot.field_evidence_rerun_callback_intake.v1`。
- 输出 summary schema `trashbot.field_evidence_rerun_callback_intake_summary.v1`。
- callback packet 必须覆盖或明确缺失以下 material classes：
  - real route completion signal
  - real field task record
  - real Nav2/fixed-route runtime log
  - real elevator door summary
  - real target floor / floor arrival summary
  - real human-assistance summary
  - real dropoff completion
  - real cancel completion
  - real delivery result
  - real phone/browser evidence
- 每个 material class 必须归类为 `accepted`、`missing`、`rejected` 或 `blocked`，并输出 `next_required_evidence`。
- 必须校验 same safe `evidence_ref` requirement；不一致时进入 `rejected` 或 `blocked`。
- 缺 dispatch 输入、缺 callback packet、坏 JSON、unsupported schema/boundary、unsafe copy、raw path、credential、ROS topic、serial/UART/WAVE ROVER detail、checksum、完整 artifact、traceback、success phrasing、`safe_to_control=true`、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 输出必须固定 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`software_proof_docker_field_evidence_rerun_callback_intake_gate`。
- 新增代码技术注释必须使用中文，且有意义中文注释比例超过 20%。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_callback_intake.py tests/test_field_evidence_rerun_callback_intake.py
python3 -m unittest tests.test_field_evidence_rerun_callback_intake
python3 pc-tools/evidence/field_evidence_rerun_callback_intake.py --help
rg -n "field_evidence_rerun_callback_intake|software_proof_docker_field_evidence_rerun_callback_intake_gate|accepted|missing|rejected|blocked|real route completion|real field task record|Nav2/fixed-route runtime log|real phone/browser|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence/field_evidence_rerun_callback_intake.py tests/test_field_evidence_rerun_callback_intake.py pc-tools docs
git diff --check -- pc-tools/evidence/field_evidence_rerun_callback_intake.py tests/test_field_evidence_rerun_callback_intake.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 新增 safe alias `robot_diagnostics_field_evidence_rerun_callback_intake_summary`。
- 消费 top-level callback intake summary、artifact nested summary、diagnostics summary、diagnostics nested summary 和 explicit ref。
- 缺失、unsafe 或 unsupported schema 时输出 blocked default summary。
- Robot alias 只读展示 intake status、safe `evidence_ref`、accepted / missing / rejected / blocked material counts、next required evidence、same-evidence-ref status、safe copy 和 proof boundary。
- 不触发 collect/dropoff/cancel、ACK、cursor、Nav2 runtime、serial/UART、WAVE ROVER、HIL 或任何 robot command。
- 保持 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- `docs/interfaces/ros_contracts.md` 必须说明该 alias 是 Robot diagnostics 只读消费，不是控制授权、delivery result、dropoff/cancel completion、field pass 或 HIL。
- 新增代码技术注释必须使用中文，且有意义中文注释比例超过 20%。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_callback_intake_summary|field_evidence_rerun_callback_intake|software_proof_docker_field_evidence_rerun_callback_intake_gate|accepted|missing|rejected|blocked|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现要求：

- 新增只读“现场证据复跑回执入口”panel。
- 优先消费 `robot_diagnostics_field_evidence_rerun_callback_intake_summary`，再消费 `field_evidence_rerun_callback_intake_summary`、artifact nested summary、diagnostics summary。
- 展示字段限定为 intake status、safe `evidence_ref`、accepted / missing / rejected / blocked material groups、next required evidence、same-evidence-ref status、safe copy、evidence boundary、`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不 fetch raw artifact，不展示 raw JSON、local path、checksum、credential、ROS topic、serial/UART、WAVE ROVER detail、完整 artifact、traceback、success copy、control authorization。
- Start Delivery / Confirm Dropoff / Cancel gating 不变。
- `docs/product/mobile_user_flow.md` 必须说明 panel 只读且不是真实手机/browser、真实 route/elevator field pass、dropoff/cancel completion、delivery success、HIL 或 O5 external proof。
- 新增代码技术注释必须使用中文，且有意义中文注释比例超过 20%。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/dev/null
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "现场证据复跑回执入口|field_evidence_rerun_callback_intake|robot_diagnostics_field_evidence_rerun_callback_intake_summary|software_proof_docker_field_evidence_rerun_callback_intake_gate|accepted|missing|rejected|blocked|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product Manager / OKR Owner Closeout

允许改动：

- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/tech-done.md`
- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/side2side_check.md`
- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 汇总 worker 实际改动和验证结果。
- 核对 Objective 5 / Objective 1 未被软件证明误上调。
- 如无真实材料，Objective 5 保持约 68%，Objective 1 保持约 81%；O2/O3/O4 也只能写 callback intake software proof，不能写真实 field pass。
- final 必须回顾本 `OKR 最低优先级核对` 是否仍成立。
- 同步 `docs/process/okr_progress_log.md`，明确本轮是 `software_proof_docker_field_evidence_rerun_callback_intake_gate`。
- Product closeout 必须核对 docs 同步：PC README / evidence contract、ROS contract、mobile user flow 都已跟随实现更新。

验收命令：

```bash
test -f sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/tech-done.md && test -f sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/side2side_check.md && test -f sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/final.md
rg -n "field_evidence_rerun_callback_intake|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_field_evidence_rerun_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake
```

## 5. 接口和数据边界

允许输入：

- `trashbot.field_evidence_rerun_material_dispatch.v1`
- `trashbot.field_evidence_rerun_material_dispatch_summary.v1`
- 现场 owner callback packet，必须引用上一轮 dispatch requirement 和同一 safe `evidence_ref`
- 兼容 wrapper / nested JSON 中的 phone-safe or diagnostics-safe summary

允许输出：

- `trashbot.field_evidence_rerun_callback_intake.v1`
- `trashbot.field_evidence_rerun_callback_intake_summary.v1`
- `robot_diagnostics_field_evidence_rerun_callback_intake_summary`
- mobile/web read-only callback intake panel

禁止输入或输出：

- raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER low-level details。
- credentials、OSS AK/SK、DB/queue URL、bearer token。
- complete raw artifact、checksum、absolute local path、traceback。
- success/control copy。
- `safe_to_control=true`。
- `delivery_success=true`。
- `primary_actions_enabled=true`。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved claim。
- O5 external proof、HIL、真实 phone/browser、真实 field pass claim。

## 6. 集成验收围栏

实现完成后由主节点只做验收判断，不直接修工程代码。集成围栏：

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_callback_intake.py tests/test_field_evidence_rerun_callback_intake.py
python3 -m unittest tests.test_field_evidence_rerun_callback_intake
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/dev/null
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "field_evidence_rerun_callback_intake|robot_diagnostics_field_evidence_rerun_callback_intake_summary|software_proof_docker_field_evidence_rerun_callback_intake_gate|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|accepted|missing|rejected|blocked|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" OKR.md docs/process/okr_progress_log.md pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake
```

## 7. 3 个并行子 Agent 启动要求

实现阶段必须在同一轮并行启动 3 个 Codex worker：

- `autonomy-engineer`：负责 Task A 文件范围和验收命令。
- `robot-software-engineer`：负责 Task B 文件范围和验收命令。
- `full-stack-software-engineer`：负责 Task C 文件范围和验收命令。

三者不是单线替代关系。Autonomy 输出 PC summary schema，Robot 只读 safe alias，Full-stack 只读消费 safe alias 或兼容 summary。若接口字段需要协调，以 Autonomy 的 summary schema 为 source of truth，Robot 和 Full-stack 只消费白名单字段。

Product closeout 在三位 Engineer 返回后再执行，不得提前把 planning docs 当业务结果。

## 8. 剩余风险和阻塞

- 本机没有真实硬件，任何 WAVE ROVER/UART/HIL 相关结论只能保持 `not_proven`。
- 本机没有真实外部云/4G/OSS/CDN/DB/queue/worker/手机材料，Objective 5 不能因本轮上调。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending，不能因 latest manual reply `3269642220` 写成 Objective 1 提升。
- PR #4 / route/elevator field materials 仍需真实现场采集；本轮 callback intake 只是接收和校验现场 owner 回执。
- 如果 callback packet 没有真实材料，最终应记录 accepted 为空或部分为空、missing/rejected/blocked 仍存在，并保持 `delivery_success=false`。

## 9. Planning Task 验收命令

```bash
test -f sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/pre_start.md && test -f sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/prd.md && test -f sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|field_evidence_rerun_callback_intake|software_proof_docker_field_evidence_rerun_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake
git diff --check -- sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake
```
