# Sprint 2026.05.16_08-09 Mobile Field Material Review Decision - Tech Plan

sprint_type: epic

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节完成度最低的是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 66%。

本 sprint 不针对 Objective 5。具体理由：

- `OKR.md` 第 6 节明确要求，只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料时才继续推进 Objective 5 completion。
- 本机没有真实硬件，只有docker；当前也没有真实公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料。
- 继续做本地 O5 metadata 会重复消费同一外部材料 blocker，不能实际提高 Objective 5。
- 最新 sprint `2026.05.16_07-08_mobile-field-material-intake` 的 final 已把下一步指向真实手机/PWA observation 或 Objective 2 / Objective 3 的 route/elevator 现场材料链。

因此本轮改推 Objective 2 / Objective 3：把 `mobile_field_material_intake` 推进为 `mobile_field_material_review_decision`，将 intake 输出转换为 phone-safe review decision、blocker、next-required-evidence 和 owner handoff。Objective 4 只作为手机入口支撑；Objective 5 不上调。

## 1. 技术总线

目标契约：

- artifact/schema：`trashbot.mobile_field_material_review_decision.v1`
- summary/schema：`trashbot.mobile_field_material_review_decision_summary.v1`
- evidence boundary：`software_proof_docker_mobile_field_material_review_decision_gate`
- 输入：`mobile_field_material_intake` artifact / summary
- 输出：review decision、blocker classification、next-required-evidence、owner handoff、safe `evidence_ref`、same-evidence-ref status、operator next steps、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

数据流：

```text
mobile_field_material_intake artifact/summary
  -> pc-tools/evidence/mobile_field_material_review_decision.py
  -> mobile_field_material_review_decision artifact/summary
  -> operator_gateway_diagnostics metadata-only consumer
  -> mobile/web read-only review decision panel
  -> Product closeout
```

边界：

- 不启用 Start Delivery、Confirm Dropoff、Cancel。
- 不发 ACK、cursor、persistence 或 robot command。
- 不证明真实手机、真实 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART 或 Objective 5 external proof。

## 2. Task A - Full-stack

Owner：`full-stack-software-engineer`

### 文件范围

允许改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

禁止改动范围外文件。

### 接口边界

- 消费 `mobile_field_material_review_decision` / `mobile_field_material_review_decision_summary`，兼容 top-level、`phone_readiness`、`/api/diagnostics`、`diagnostics.summary`、nested diagnostics summary。
- 面板只读，展示 review decision、blocker、next-required-evidence、owner handoff、safe `evidence_ref`、same-evidence-ref status、not_proven、evidence boundary。
- Copy/export 必须 whitelist-only。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 禁止展示 raw artifact、本地路径、credentials、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、DB/queue URL、OSS AK/SK、traceback、checksum 或 success wording。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "mobile_field_material_review_decision|software_proof_docker_mobile_field_material_review_decision_gate|review decision|owner handoff|next-required-evidence|delivery_success=false|primary_actions_enabled=false|not_proven" mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 3. Task B - Robot

Owner：`robot-software-engineer`

### 文件范围

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

禁止改动范围外文件。

### 接口边界

- 新增 diagnostics metadata-only consumer：`mobile_field_material_review_decision` 和 `mobile_field_material_review_decision_summary`。
- 支持 explicit ref、environment variable 或 diagnostics source；建议 env 名使用 `TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION`。
- 接受 schema `trashbot.mobile_field_material_review_decision.v1` 或 summary schema。
- 强制 evidence boundary 为 `software_proof_docker_mobile_field_material_review_decision_gate`。
- 输出只用于 diagnostics / phone readiness metadata；不触发 command、ACK、cursor、persistence、Nav2/fixed-route、HIL、dropoff/cancel completion 或 delivery success。
- unsafe success claim、bad JSON、missing、unsupported schema、unsafe copy 必须 fail closed。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_field_material_review_decision|software_proof_docker_mobile_field_material_review_decision_gate|TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION|delivery_success=false|primary_actions_enabled=false|not_proven|metadata-only" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 4. Task C - Autonomy

Owner：`autonomy-engineer`

### 文件范围

允许改动：

- `pc-tools/evidence/mobile_field_material_review_decision.py`
- `pc-tools/evidence/test_mobile_field_material_review_decision.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

禁止改动范围外文件。

### 接口边界

- 输入上一轮 `mobile_field_material_intake` artifact / summary。
- 输出 `trashbot.mobile_field_material_review_decision.v1` artifact 和 summary-compatible payload。
- 必须保留 same `evidence_ref`，并对 mismatch / missing / placeholder / unsafe success wording fail closed。
- 决策必须至少覆盖：
  - blocked_missing_real_phone_or_pwa_observation
  - blocked_missing_route_elevator_field_materials
  - blocked_missing_nav2_or_fixed_route_runtime_log
  - blocked_missing_same_evidence_ref_task_record_or_completion_signal
  - blocked_missing_dropoff_or_cancel_completion
  - ready_for_owner_handoff_not_proven
- owner handoff 必须映射到 Full-stack、Robot、Autonomy 或 Product closeout。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/mobile_field_material_review_decision.py pc-tools/evidence/test_mobile_field_material_review_decision.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_mobile_field_material_review_decision.py
python3 pc-tools/evidence/mobile_field_material_review_decision.py --help
rg -n "mobile_field_material_review_decision|software_proof_docker_mobile_field_material_review_decision_gate|next-required-evidence|owner handoff|blocked_missing|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence/mobile_field_material_review_decision.py pc-tools/evidence/test_mobile_field_material_review_decision.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/mobile_field_material_review_decision.py pc-tools/evidence/test_mobile_field_material_review_decision.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

## 5. Task D - Product Closeout

Owner：`product-okr-owner`

### 文件范围

允许改动：

- `sprints/2026.05.16_08-09_mobile-field-material-review-decision/tech-done.md`
- `sprints/2026.05.16_08-09_mobile-field-material-review-decision/side2side_check.md`
- `sprints/2026.05.16_08-09_mobile-field-material-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

禁止改动范围外文件。

### 接口边界

- 收口只在 A/B/C 完成并返回验证结果后进行。
- `OKR.md` 只按实际验证结果保守更新；Objective 5 没有真实外部材料不得上调。
- final 必须写清 `software_proof_docker_mobile_field_material_review_decision_gate` 不等于真实手机、真实 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL 或 Objective 5 external proof。
- 提交前显式排除无关 worktree churn。

### 验收命令

```bash
rg -n "mobile_field_material_review_decision|Objective 5|Objective 2|Objective 3|software_proof_docker_mobile_field_material_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|不证明|真实公网|只有docker|PR|评审" sprints/2026.05.16_08-09_mobile-field-material-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_08-09_mobile-field-material-review-decision OKR.md docs/process/okr_progress_log.md
```

## 6. 并行启动要求

A Full-stack、B Robot、C Autonomy 文件范围互不重叠，必须并行启动 3 个 worker。D Product closeout 等 A/B/C 返回后执行，不与实现并行改 `OKR.md` 或 closeout 文档。

本轮为 Epic sprint，预计跨 3 个 Engineer + Product closeout，目标是新增完整 review decision 能力模块；不得降级为 1 个 worker 单线完成 2+ owner sprint。

## 7. Planning 文件验收命令

```bash
test -f sprints/2026.05.16_08-09_mobile-field-material-review-decision/pre_start.md && test -f sprints/2026.05.16_08-09_mobile-field-material-review-decision/prd.md && test -f sprints/2026.05.16_08-09_mobile-field-material-review-decision/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 2|Objective 3|mobile_field_material_review_decision|software_proof_docker_mobile_field_material_review_decision_gate|本机没有真实硬件|只有docker|PR|评审" sprints/2026.05.16_08-09_mobile-field-material-review-decision
git diff --check -- sprints/2026.05.16_08-09_mobile-field-material-review-decision
```

## 8. 剩余风险

- 本轮计划不能替代实现结果，不能单独更新 OKR。
- 如果 A/B/C 任一实现缺少 metadata-only / fail-closed 证据，D 不得上调 Objective 2 / Objective 3。
- 如果真实外部 O5 证据仍缺失，Objective 5 必须保持约 66%。
- 如果真实手机、真实 route/elevator、Nav2/fixed-route、dropoff/cancel 或 delivery result 仍缺失，final 必须保留 `not_proven` 和对应缺口。
