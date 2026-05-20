# Sprint 2026.05.20_12-13 Field Evidence Rerun Material Dispatch - Tech Plan

## 1. 目标

实现 `field_evidence_rerun_material_dispatch`：把 O5 / O1 / O4 不能继续本地堆 metadata 的 blocker，转成 Objective 2 / 3 / 4 现场 rerun 的跨 owner 真实材料派发包。派发包必须列出同一 safe `evidence_ref` 下必须由现场 owner 回填或重跑的真实 route completion、task record、Nav2/fixed-route runtime log、电梯门/楼层/人工协助 summaries、dropoff/cancel completion、delivery result 和真实手机/browser evidence。

证据边界固定为：

- `software_proof_docker_field_evidence_rerun_material_dispatch_gate`

固定输出安全状态：

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对理由：Objective 5 只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料才能继续提高；本机只有 Docker，不能继续堆本地 O5 metadata depth。
4. 当前次低 Objective 是 Objective 1，约 81%。本 sprint 不直接提高 Objective 1，因为 PR #5 `PRRT_kwDOSWB9286CJ3tX` live 状态仍 unresolved / `is_resolved=false` / material pending；Q/U 已 resolved，但 reply publication 或 vendor-source citation reply 不能作为 O1 提升。
5. 最新 sprint `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/final.md` 完成 `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff`，只推进 O4 phone-safe handoff chain，OKR 百分比不提高；继续同义 handoff wrapper 会重复消费真实手机/browser blocker。
6. 2026-05-18 route/elevator rerun chain 已推进到 `route_task_field_retest_acceptance_execution_rerun_result_review_handoff`，且 2026-05-19 real-material followup/escalation/status 已明确下一步需要现场 owner 提交真实材料。本轮选择 `field_evidence_rerun_material_dispatch`，把这个缺口转成可执行派发包。

## 3. PR / sprint 证据基础

- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser；本轮不得声明 O5 external proof。
- Objective 1 仍缺真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 `PRRT_kwDOSWB9286CJ3tX` 需要的真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 最新 O4 sprint 已做 handoff review handoff，但仍不是真实手机/browser 或 production app 验收。
- route/elevator material chain 已多次证明本地 metadata 可读，但真实材料仍未提交；本轮要把“缺什么、谁补、怎么 rerun、三方怎么验收”落成派发包。

## 4. 并行 owner / file scope

本轮是 Epic sprint。实现阶段默认并行启动 3 个 Engineer worker，Product 后置 closeout。Autonomy、Robot、Full-stack 文件范围互不重叠；Product 只做收口文档和 OKR/progress log。

### Task A - Autonomy Algorithm Engineer

允许改动：

- `pc-tools/evidence/field_evidence_rerun_material_dispatch.py`
- `tests/test_field_evidence_rerun_material_dispatch.py`
- `pc-tools/README.md` 或现有 evidence gate 索引文档中对应段落
- `docs/architecture/evidence_contracts.md` 或现有同类 evidence contract 文档

实现要求：

- 只读消费最近 route/elevator rerun review handoff、real-material followup/escalation/status 或兼容 summary。
- 输出 artifact schema `trashbot.field_evidence_rerun_material_dispatch.v1`。
- 输出 summary schema `trashbot.field_evidence_rerun_material_dispatch_summary.v1`。
- 必须列出 required material groups：
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
- 必须输出 owner work orders、rerun commands、callback packet requirements、same safe `evidence_ref` requirement、safe copy 和 fail-closed status。
- 缺输入、坏 JSON、unsupported schema/boundary、source 不在 `not_proven`/software proof 范围、unsafe copy、raw path、credential、ROS topic、serial/UART/WAVE ROVER detail、checksum、完整 artifact、success phrasing、`safe_to_control=true`、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 新增代码技术注释必须使用中文，且有意义中文注释比例超过 20%。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_material_dispatch.py tests/test_field_evidence_rerun_material_dispatch.py
python3 -m unittest tests.test_field_evidence_rerun_material_dispatch
python3 pc-tools/evidence/field_evidence_rerun_material_dispatch.py --help
rg -n "field_evidence_rerun_material_dispatch|software_proof_docker_field_evidence_rerun_material_dispatch_gate|real route completion|real field task record|Nav2/fixed-route runtime log|real phone/browser|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence/field_evidence_rerun_material_dispatch.py tests/test_field_evidence_rerun_material_dispatch.py pc-tools docs
git diff --check -- pc-tools/evidence/field_evidence_rerun_material_dispatch.py tests/test_field_evidence_rerun_material_dispatch.py pc-tools docs
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 新增 safe alias `robot_diagnostics_field_evidence_rerun_material_dispatch_summary`。
- 消费 top-level dispatch summary、artifact nested summary、status diagnostics summary、diagnostics nested summary 和 explicit ref。
- 缺失、unsafe 或 unsupported schema 时输出 blocked default summary。
- 不触发 collect/dropoff/cancel、ACK、cursor、Nav2 runtime、serial/UART、WAVE ROVER、HIL 或任何 robot command。
- 保持 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- `docs/interfaces/ros_contracts.md` 必须说明该 alias 是 Robot diagnostics 只读消费，不是控制授权、delivery result 或 HIL。
- 新增代码技术注释必须使用中文，且有意义中文注释比例超过 20%。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_material_dispatch_summary|field_evidence_rerun_material_dispatch|software_proof_docker_field_evidence_rerun_material_dispatch_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
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

- 新增只读“现场证据复跑材料派发”panel。
- 优先消费 `robot_diagnostics_field_evidence_rerun_material_dispatch_summary`，再消费 `field_evidence_rerun_material_dispatch_summary`、artifact nested summary、diagnostics summary。
- 展示字段限定为 dispatch status、safe `evidence_ref`、owner work orders、required material groups、rerun commands、callback packet requirements、same-evidence-ref status、safe copy、evidence boundary、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不 fetch raw artifact，不展示 raw JSON、local path、checksum、credential、ROS topic、serial/UART、WAVE ROVER detail、完整 artifact、success copy、control authorization。
- Start Delivery / Confirm Dropoff / Cancel gating 不变。
- `docs/product/mobile_user_flow.md` 必须说明 panel 只读且不是真实手机/browser、真实 route/elevator field pass、dropoff/cancel completion、delivery success、HIL 或 O5 external proof。
- 新增代码技术注释必须使用中文，且有意义中文注释比例超过 20%。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/dev/null
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "现场证据复跑材料派发|field_evidence_rerun_material_dispatch|robot_diagnostics_field_evidence_rerun_material_dispatch_summary|software_proof_docker_field_evidence_rerun_material_dispatch_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product Manager / OKR Owner Closeout

允许改动：

- `sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/tech-done.md`
- `sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/side2side_check.md`
- `sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 汇总 worker 实际改动和验证结果。
- 核对 Objective 5 / Objective 1 未被软件证明误上调。
- 如无真实材料，Objective 5 保持约 68%，Objective 1 保持约 81%；O2/O3/O4 也只能写软件证明层收益，不能写真实 field pass。
- final 必须回顾本 `OKR 最低优先级核对` 是否仍成立。
- 同步 `docs/process/okr_progress_log.md`，明确本轮是 `software_proof_docker_field_evidence_rerun_material_dispatch_gate`。

验收命令：

```bash
test -f sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/tech-done.md && test -f sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/side2side_check.md && test -f sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/final.md
rg -n "field_evidence_rerun_material_dispatch|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_field_evidence_rerun_material_dispatch_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch
```

## 5. 接口和数据边界

允许输入：

- `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff.v1`
- `trashbot.real_material_followup_escalation_status_summary.v1`
- `trashbot.real_material_evidence_intake_summary.v1`
- `trashbot.real_material_manifest_template_summary.v1`
- 兼容 wrapper / nested JSON 中的 phone-safe or diagnostics-safe summary

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
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_material_dispatch.py tests/test_field_evidence_rerun_material_dispatch.py
python3 -m unittest tests.test_field_evidence_rerun_material_dispatch
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/dev/null
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "field_evidence_rerun_material_dispatch|robot_diagnostics_field_evidence_rerun_material_dispatch_summary|software_proof_docker_field_evidence_rerun_material_dispatch_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" OKR.md docs/process/okr_progress_log.md pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch
git diff --check -- OKR.md docs/process/okr_progress_log.md pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch
```

## 7. 剩余风险和阻塞

- 本机没有真实硬件，任何 WAVE ROVER/UART/HIL 相关结论只能保持 `not_proven`。
- 本机没有真实外部云/4G/OSS/CDN/DB/queue/worker/手机材料，Objective 5 不能因本轮上调。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending，不能因 reply publication 或 vendor-source citation reply 写成 Objective 1 提升。
- PR #4 / route/elevator field materials 仍需真实现场采集；本轮 dispatch package 只是把下一步 owner work orders、rerun commands 和 callback packet requirements 明确化。
- 如果 worker 实现发现输入 family 不足，优先 fail closed，并在 `tech-done.md` 写明需要哪类真实材料或 schema backfill。
