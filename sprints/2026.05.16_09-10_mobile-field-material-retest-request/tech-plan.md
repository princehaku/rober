# Sprint 2026.05.16_09-10 Mobile Field Material Retest Request - Tech Plan

sprint_type: epic

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节完成度最低的是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 66%。

本 sprint 不针对 Objective 5。具体理由：

- Objective 5 的下一步真实进展需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- 当前本机没有真实硬件，只有docker；也没有公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料。
- 继续做本地 O5 metadata 会重复消费同一外部材料 blocker，不能提高真实 O5 product proof。
- `OKR.md` 第 6 节已经把当前最高可行动作指向使用 `mobile_field_material_review_decision` 输出的 blocker / next-required-evidence / owner handoff 去补真实手机材料或 Objective 2 / Objective 3 的 route/elevator 现场材料链。

本轮主线为 Objective 2 / Objective 3：把 08-09 review decision 继续推进为 route/elevator field retest request。Objective 4 只做手机只读支撑；Objective 1 / Objective 5 不上调。

## 1. 技术总线

目标契约：

- artifact/schema：`trashbot.mobile_field_material_retest_request.v1`
- summary/schema：`trashbot.mobile_field_material_retest_request_summary.v1`
- evidence boundary：`software_proof_docker_mobile_field_material_retest_request_gate`
- 输入：`mobile_field_material_review_decision` artifact / summary
- 输出：source review decision、blockers、next_required_evidence、retest_request、route/elevator material checklist、owner handoff、safe `evidence_ref`、same_evidence_ref_required/status、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

数据流：

```text
mobile_field_material_review_decision artifact/summary
  -> pc-tools/evidence/mobile_field_material_retest_request.py
  -> mobile_field_material_retest_request artifact/summary
  -> operator_gateway_diagnostics metadata-only consumer
  -> mobile/web read-only retest request panel
  -> Product closeout after worker evidence
```

边界：

- 不启用 Start Delivery、Confirm Dropoff、Cancel。
- 不发 ACK、cursor、persistence 或 robot command。
- 不证明真实手机、真实 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART 或 Objective 5 external proof。
- 不读取或展示 raw artifact、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、credentials、DB/queue URL、OSS AK/SK、local path、traceback、checksum 或 complete artifact。

## 2. Task A - Autonomy Retest Request Gate

Owner：`autonomy-engineer`

### 文件范围

允许改动：

- `pc-tools/evidence/mobile_field_material_retest_request.py`
- `pc-tools/evidence/test_mobile_field_material_retest_request.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

禁止改动范围外文件。

### 接口边界

- 输入上一轮 `mobile_field_material_review_decision` artifact / summary。
- 输出 `trashbot.mobile_field_material_retest_request.v1` artifact 和 `trashbot.mobile_field_material_retest_request_summary.v1` summary-compatible payload。
- 必须保留 source review decision、blockers、next_required_evidence 和 owner handoff。
- 必须要求 same `evidence_ref`，并输出 `same_evidence_ref_required=true` 和 `same_evidence_ref_status`。
- 必须生成 route/elevator material checklist，至少覆盖：
  - door state material
  - target floor confirmation
  - human assistance note
  - Nav2/fixed-route runtime log
  - task record
  - completion signal
  - dropoff/cancel completion material
  - mobile/diagnostics safe summary
- missing / mismatch / placeholder / unsafe success wording / unsupported schema 必须 fail closed。
- 输出必须固定 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/mobile_field_material_retest_request.py pc-tools/evidence/test_mobile_field_material_retest_request.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_mobile_field_material_retest_request.py
python3 pc-tools/evidence/mobile_field_material_retest_request.py --help
rg -n "mobile_field_material_retest_request|software_proof_docker_mobile_field_material_retest_request_gate|retest request|next_required_evidence|route/elevator material checklist|same_evidence_ref_required|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence/mobile_field_material_retest_request.py pc-tools/evidence/test_mobile_field_material_retest_request.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/mobile_field_material_retest_request.py pc-tools/evidence/test_mobile_field_material_retest_request.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

## 3. Task B - Robot Diagnostics Metadata-Only Consumer

Owner：`robot-software-engineer`

### 文件范围

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

禁止改动范围外文件。

### 接口边界

- 新增 diagnostics metadata-only consumer：`mobile_field_material_retest_request` 和 `mobile_field_material_retest_request_summary`。
- 支持 explicit ref、environment variable 或 diagnostics source；建议 env 名使用 `TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST`。
- 接受 schema `trashbot.mobile_field_material_retest_request.v1` 或 `trashbot.mobile_field_material_retest_request_summary.v1`。
- 强制 evidence boundary 为 `software_proof_docker_mobile_field_material_retest_request_gate`。
- 输出只用于 diagnostics / phone readiness metadata；不触发 command、ACK、cursor、persistence、Nav2/fixed-route、HIL、dropoff/cancel completion 或 delivery success。
- unsafe success claim、bad JSON、missing、unsupported schema、unsafe copy、boundary mismatch 必须 fail closed。
- 必须保留 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_field_material_retest_request|software_proof_docker_mobile_field_material_retest_request_gate|TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST|delivery_success=false|primary_actions_enabled=false|not_proven|metadata-only" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 4. Task C - Full-stack Read-Only Request Panel

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

- 消费 `mobile_field_material_retest_request` / `mobile_field_material_retest_request_summary`，兼容 top-level、`phone_readiness`、`/api/diagnostics`、`diagnostics.summary`、`diagnostics.diagnostics_summary`、nested diagnostics summary 和 status diagnostics summary。
- 面板只读，展示 source review decision、blockers、next-required-evidence、retest request、route/elevator material checklist、owner handoff、safe `evidence_ref`、same-evidence-ref status、`not_proven`、evidence boundary。
- Copy/export 必须 whitelist-only。
- 缺 summary 时显示 blocked/not_proven。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 禁止展示 raw artifact、本地路径、credentials、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、DB/queue URL、OSS AK/SK、traceback、checksum、complete artifact 或 success wording。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "mobile_field_material_retest_request|software_proof_docker_mobile_field_material_retest_request_gate|retest request|owner handoff|next-required-evidence|route/elevator material checklist|delivery_success=false|primary_actions_enabled=false|not_proven" mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 5. Task D - Product Closeout

Owner：`product-okr-owner`

### 文件范围

允许改动：

- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/tech-done.md`
- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/side2side_check.md`
- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

禁止改动范围外文件。

### 接口边界

- 收口只在 A/B/C 完成并返回验证结果后进行。
- `OKR.md` 只按实际验证结果保守更新；Objective 1 / Objective 5 没有真实硬件或真实外部材料不得上调。
- final 必须写清 `software_proof_docker_mobile_field_material_retest_request_gate` 不等于真实手机、真实 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL、真实 WAVE ROVER/UART 或 Objective 5 external proof。
- Product closeout 必须同步确认 `docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`、`docs/navigation/fixed_route_workflow.md`、`pc-tools/README.md` 是否随实际实现更新。
- 提交前显式排除无关 worktree churn。

### 验收命令

```bash
rg -n "mobile_field_material_retest_request|Objective 5|Objective 2|Objective 3|software_proof_docker_mobile_field_material_retest_request_gate|not_proven|delivery_success=false|primary_actions_enabled=false|不证明|真实公网|只有docker|真实 WAVE ROVER|PR|评审" sprints/2026.05.16_09-10_mobile-field-material-retest-request OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_09-10_mobile-field-material-retest-request OKR.md docs/process/okr_progress_log.md
```

## 6. 并行启动要求

Task A Autonomy、Task B Robot、Task C Full-stack 文件范围互不重叠，必须并行启动 3 个 worker。Task D Product closeout 等 A/B/C 返回后执行，不与实现并行改 `OKR.md` 或 closeout 文档。

本轮为 Epic sprint，跨 3 个 Engineer + Product closeout，目标是新增完整 retest request 能力模块；不得降级为 1 个 worker 单线完成 2+ owner sprint。

后续 Codex worker prompt 必须包含：

- 角色 System Prompt：从 `.codex/agents/<role>.toml` 的 `prompt` 字段完整复制；若 role file 不存在，使用 repo-local `AGENTS.md` 对应角色职责。
- 本轮任务：明确目标是 `mobile_field_material_retest_request`，不是 delivery success 或 O5 external proof。
- 文件范围：只列对应 task 的允许文件。
- 验收命令：复制本计划对应 task 的命令。
- 输出要求：实际改动文件、验证命令输出、失败定位、剩余风险。

## 7. Planning 文件验收命令

```bash
test -f sprints/2026.05.16_09-10_mobile-field-material-retest-request/pre_start.md && test -f sprints/2026.05.16_09-10_mobile-field-material-retest-request/prd.md && test -f sprints/2026.05.16_09-10_mobile-field-material-retest-request/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 2|Objective 3|review decision|retest request|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|只有docker|真实公网|真实 WAVE ROVER|PR|评审" sprints/2026.05.16_09-10_mobile-field-material-retest-request
git diff --check -- sprints/2026.05.16_09-10_mobile-field-material-retest-request
```

## 8. 剩余风险

- 本轮 planning 不能替代实现结果，不能单独更新 OKR。
- 如果 A/B/C 任一实现缺少 metadata-only / fail-closed 证据，D 不得上调 Objective 2 / Objective 3。
- 如果真实外部 O5 证据仍缺失，Objective 5 必须保持约 66%。
- 如果真实 WAVE ROVER/UART/HIL 仍缺失，Objective 1 不得上调。
- 如果真实手机、真实 route/elevator、Nav2/fixed-route、dropoff/cancel 或 delivery result 仍缺失，final 必须保留 `not_proven` 和对应缺口。
