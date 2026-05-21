# Field Evidence Rerun Execution Result Acceptance Packet Tech Done

## Autonomy Evidence Section

### 自主能力目标和本轮抓手

- 目标：新增 PC evidence gate `field_evidence_rerun_execution_result_acceptance_packet`，把上一轮 review handoff 和 field owner 脱敏 acceptance packet 收口到同一 safe `evidence_ref` 下的验收 readiness。
- 抓手：固定 `required_materials=task_record, nav2_fixed_route_runtime_log, route_completion_signal, elevator_evidence, dropoff_cancel_completion, delivery_result, true_phone_browser_evidence, diagnostics_mobile_safe_summary`，并保持 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

### 实际改动

- 新增 `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_packet.py`：读取 safe review handoff 和 safe acceptance packet，输出 artifact/summary schemas `trashbot.field_evidence_rerun_execution_result_acceptance_packet.v1` 与 `trashbot.field_evidence_rerun_execution_result_acceptance_packet_summary.v1`。
- 新增 `pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_packet.py`：覆盖 ready、missing packet、missing material、non-ready handoff、evidence_ref mismatch、unsafe copy、success/control claim 和 nested wrapper。
- 更新 `pc-tools/README.md` 与 `docs/interfaces/evidence_contracts.md`：记录 CLI、schema、required materials、allowed verdicts 和 software-proof 边界。

### 接口影响

- 新增 PC-only CLI：
  `python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_packet.py --review-handoff-json <handoff.json> --acceptance-packet-json <packet.json> --evidence-ref <same_ref>`.
- 新增 verdicts：`ready_for_field_owner_acceptance_review_not_proven`、`needs_material_backfill`、`blocked_evidence_ref_mismatch`、`blocked_unsafe_material`、`rejected_success_claim`、`blocked_missing_acceptance_packet`。
- 不改 ROS2 action、TrashStatus、Robot diagnostics、mobile/web、OKR 或硬件配置。

### 验证结果

- `python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_packet.py`：通过，exit 0。
- `python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_packet.py`：通过，`Ran 4 tests in 0.039s OK`。第一轮曾发现 `delivery_success=true` 嵌套 bool 未被拒绝，已修复 `_success_claim` 并复跑通过。
- `python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_packet.py --help`：通过，显示 `--review-handoff-json`、`--acceptance-packet-json`、`--evidence-ref`、`--output`、`--summary-output` 和 `--once-json`。
- `rg -n "field_evidence_rerun_execution_result_acceptance_packet|software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate|same_evidence_ref|required_materials|task record|Nav2|fixed-route|route completion signal|elevator evidence|dropoff|cancel|delivery result|true phone|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-done.md`：通过，exit 0，匹配到新增 gate、测试、README、interface contract 和本 Autonomy section。
- `git diff --check -- pc-tools/evidence pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-done.md`：通过，exit 0。

### 数据、样本或调试输出变化

- 新增 artifact/summary 中的 `accepted_materials`、`missing_materials`、`rejected_materials`、`acceptance_gap_summary`、`owner_handoff`、`next_required_evidence` 和 `safe_copy`，方便后续 Robot/mobile 只读消费。
- 不新增真实现场样本，不读取 raw task record、raw Nav2/fixed-route runtime、raw elevator evidence、raw dropoff/cancel、raw delivery result 或 true phone/browser runtime。

### 剩余风险

- 该 gate 只证明本地 Docker/PC `software_proof` 合同可复跑，不证明真实 field rerun、真实 Nav2/fixed-route、真实 route completion signal、真实 elevator evidence、真实 dropoff/cancel completion、真实 delivery result、真实 phone/browser、HIL 或 delivery success。
- 后续仍需 Robot worker 建立 safe diagnostics alias，Full-Stack worker 建立 mobile/web 只读 panel，Product worker 做 OKR conservative closeout。

## Full-Stack Evidence Section

### 用户触点目标和本轮抓手

- 目标：在 mobile/web 增加 `field_evidence_rerun_execution_result_acceptance_packet` read-only panel，让现场 owner/support 能在手机首屏看到验收包 readiness、缺失材料、阻塞材料和下一步，而不用读取 raw diagnostics/artifacts。
- 抓手：优先消费 `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary`，fallback 只接受同名 safe summary；保持 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

### 实际改动

- 更新 `mobile/web/app.js`：新增 acceptance packet safe resolver、unsafe 文本围栏、只读 panel 和渲染链路，显示 packet verdict、source review handoff、safe `evidence_ref`、same-evidence-ref status、accepted/missing/blocked materials、owner next steps、safe copy 和 proof boundary。
- 新增 `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet.json`：覆盖 Robot safe alias 与 fallback summary，三类主操作均保持 disabled。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`：新增 fail-closed panel 测试和 phone-safe fixture 测试，确认不新增 raw diagnostics/artifacts、ACK/cursor、command replay、resubmit、control endpoint、copy/download/submit/replay/resubmit 按钮。
- 更新 `docs/product/mobile_user_flow.md`：同步记录新 panel 的 summary schema、fallback 顺序、展示字段、禁止行为和 evidence boundary。

### 接口影响

- 新增 mobile/web 消费字段：`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary`。
- 兼容 fallback 字段：`field_evidence_rerun_execution_result_acceptance_packet_summary`、`field_evidence_rerun_execution_result_acceptance_packet.summary`、diagnostics summary / nested diagnostics summary / status diagnostics summary 中的同名 summary。
- 不新增 fetch raw diagnostics/artifacts，不新增 ACK/cursor/command/replay/resubmit/control endpoint，不改变 Start Delivery / Confirm Dropoff / Cancel gating。

### 验证结果

- `node --check mobile/web/app.js`：通过。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：通过，`Ran 207 tests in 1.574s` / `OK`。首轮失败定位为 fixture 文案含 `ACK/cursor` / `command replay` 禁词，已改为不携带这些语义后重跑通过。
- `python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet.json >/tmp/field_evidence_acceptance_packet_fixture_check.json`：通过。
- `rg -n "field_evidence_rerun_execution_result_acceptance_packet|software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate|现场证据复跑执行结果验收包|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|Start Delivery|Confirm Dropoff|Cancel|true phone/browser" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-done.md`：通过，命中 app/test/fixture/docs/tech-done。
- `git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-done.md`：通过。

### 剩余风险

- 本 panel 是 mobile/web `software_proof` only，不是真实 route/elevator field pass、真实 delivery result、delivery success、true phone/browser proof、HIL、PR #5 hardware proof 或 Objective 5 external proof。
- Robot worker 仍需提供同名 safe alias summary；mobile/web 故意拒绝 raw acceptance packet 和 raw execution materials。

## Robot Evidence Section

Run time: 2026-05-21 11:15 CST

### Robot 目标和本轮抓手

- 目标：新增 Robot diagnostics safe alias `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary`，让 operator diagnostics 只读消费 canonical acceptance packet safe summary。
- 抓手：只接收 `trashbot.field_evidence_rerun_execution_result_acceptance_packet_summary.v1` 或 artifact 内嵌同名 safe summary，不消费 raw task records、raw logs、raw route/elevator artifacts 或 complete packets；保持 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate`、`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

### 实际改动

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：新增 acceptance packet schema/gate 常量、fail-closed 默认摘要、safe summary source contract、unsafe field guard、summary builder、environment/status source fallback、`latest_status` raw-field scrub 和 diagnostics payload 三个 alias 字段。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：新增 focused test，覆盖 canonical summary、nested safe summary、missing summary、unsupported schema/boundary、same-`safe_evidence_ref` mismatch、raw material blocking、latest_status raw scrub 和 fail-closed false flags。
- 更新 `docs/interfaces/ros_runtime_contracts.md`：记录 Robot-visible whitelist、forbidden raw/task/log/artifact/control material、PR #5 `PRRT_kwDOSWB9286CJ3tX` 和 comment `3269642220` 不得被写成 reviewer resolution。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：通过，exit 0。
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：通过，`Ran 255 tests in 0.900s` / `OK`。首轮失败定位为 new raw field 未加入 `latest_status` scrub，第二轮失败定位为 nested summary key 被 unsafe-key guard 误拦截；均已修复并复跑通过。
- `rg -n "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary|field_evidence_rerun_execution_result_acceptance_packet|software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX|3269642220" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-done.md`：通过，exit 0。
- `git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-done.md`：通过，exit 0。

### 剩余风险

- 该 Robot alias 是 `software_proof` / metadata-only，不证明真实 task record、Nav2/fixed-route runtime log、route completion signal、elevator evidence、dropoff/cancel completion、delivery result、true phone/browser evidence、WAVE ROVER/UART/HIL、PR #5 review resolution 或 delivery success。
- 不需要 Hardware、Autonomy 或 Full-Stack 追加协同来完成本 Robot alias；Product closeout 仍需在所有 worker evidence 返回后保守收口 OKR。

## Product Closeout Section

Run time: 2026-05-21 11:22 CST

### 用户价值和产品北极星

- 用户价值：现场 owner 和支持同学现在有一个“现场证据复跑执行结果验收包”入口，可以明确看到同一 safe `evidence_ref` 下哪些真实材料已齐、哪些仍缺、哪些被拒绝，避免把分散 handoff/review artifact 误读成真实交付结果。
- 产品北极星：`rober` 的送垃圾闭环必须由真实 route/elevator/task/phone evidence 接受，而不是由本地 wrapper 名称接受；本 sprint 只把验收材料入口做清楚。

### OKR 映射和 KR 拆解

- Objective 5：仍约 68%。本轮 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate` 不是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser proof。
- Objective 1：仍约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` still unresolved/material pending；comment `3269642220` not reviewer resolution；本轮不是 WAVE ROVER/UART/HIL 或真实 2D LiDAR / ToF source material。
- Objective 2/O3/O4：仍约 99%。本轮只新增 acceptance readiness gate / Robot safe alias / mobile read-only panel；不是真实 route/elevator field pass、not delivery result、not delivery success、not true phone/browser proof。

KR closeout:

- KR-A：Autonomy gate 已输出 acceptance packet artifact/summary schema，并要求 same safe `evidence_ref`。
- KR-B：required materials 已固定为 task record、Nav2/fixed-route runtime log、route completion signal、elevator evidence、dropoff/cancel completion、delivery result、true phone/browser evidence、diagnostics/mobile safe summary。
- KR-C：Robot diagnostics 只暴露 safe alias `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary`。
- KR-D：mobile/web 只读 panel 已展示 verdict、safe `evidence_ref`、accepted/missing/blocked materials、owner next steps，并保持 Start Delivery / Confirm Dropoff / Cancel disabled。
- KR-E：OKR closeout 未上调任何百分比。

### 本轮核心抓手和责任 Engineer

- Autonomy Algorithm Engineer：PC evidence gate、schema、CLI、focused tests、README 和 `docs/interfaces/evidence_contracts.md`。
- Robot Platform Engineer：Robot diagnostics safe alias、redaction tests、`docs/interfaces/ros_runtime_contracts.md`。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、tests、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：`OKR.md`、`docs/process/okr_progress_log.md`、`side2side_check.md`、`final.md` 和本 closeout section。

### 验收口径和证据边界

- 必须保留：`field_evidence_rerun_execution_result_acceptance_packet`、`software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate`、`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 明确不是：真实 route/elevator field pass、delivery result、delivery success、true phone/browser proof、O5 external proof、HIL、WAVE ROVER/UART proof、PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution。
- 下一步只有在真实外部 O5 材料、真实 O1 硬件/HIL 材料，或真实 same-safe-`evidence_ref` field materials 出现时才提升 OKR；否则不要重复本地 wrapper。

### Product 验证结果

- `test -f .../tech-done.md`：通过。
- `test -f .../side2side_check.md`：通过。
- `test -f .../final.md`：通过。
- required `rg`：通过，命中 OKR、progress log 和本 sprint closeout 文档中的 capability、proof boundary、Objective 5 / Objective 1、PR thread/comment、安全 flags 和 true phone/browser 边界。
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet`：通过。

### 剩余风险

- 真实材料仍未出现：真实 task record、Nav2/fixed-route runtime log、route completion signal、elevator evidence、dropoff/cancel completion、delivery result、true phone/browser evidence。
- O5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover 和 production app/device proof。
- O1 仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR / ToF source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，以及 PR #5 reviewer resolution。
