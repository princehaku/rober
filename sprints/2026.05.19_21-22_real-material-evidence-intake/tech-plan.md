# Sprint 2026.05.19_21-22 Real Material Evidence Intake - Tech Plan

## 1. Sprint 类型和实现原则

- sprint_type: epic
- 本轮新增 `real_material_evidence_intake` 统一真实材料回填 intake。
- 计划拆为 3 个并行 owner，文件范围互不重叠，符合 team 并行推进要求。
- 当前环境只有 Docker，没有真实硬件、真实手机、真实公网、4G/SIM、OSS/CDN live traffic 或 production DB/queue。所有验证只作为 `software_proof`，不声明真实材料已通过。
- 所有技术注释必须使用中文，注释用于解释为什么 fail closed、为什么过滤字段、为什么不能把 intake 当成真实通过。

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 里完成度最低的是 Objective 5，约 68%。下一低项是 Objective 1，约 81%。
2. 本 sprint 直接针对 Objective 5 的真实 external proof 缺口，同时覆盖 Objective 1 / PR #5 hardware、PR #4 route/elevator 和 Objective 4 real phone 的真实材料回填入口。
3. 选择 `real_material_evidence_intake` 的理由：
   - Objective 5 数字最低，但继续提高需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover 或真实 external proof；Docker-only 主机不能产生这些材料。
   - Objective 1 次低，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry，也缺 WAVE ROVER/UART/HIL。
   - 上一轮 `real_material_readiness_board` 已完成四类缺口展示，继续做展示会重复消费 blocker；下一步必须提供统一 intake，让真实材料到位时能回填、归档和复核。
   - PR #4 / route/elevator 与 O4 real-phone 链已多轮 wrapper，本轮只做跨 Objective 的真实材料回填入口，不再做单一缺口 wrapper。

## 3. 接口和证据合同

新增 PC artifact schema：

- artifact schema：`trashbot.real_material_evidence_intake.v1`
- summary schema：`trashbot.real_material_evidence_intake_summary.v1`
- evidence boundary：`software_proof_docker_real_material_evidence_intake_gate`
- source：`software_proof`
- required fail-closed fields：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`

Material groups：

- `o5_external`: HTTPS/TLS public ingress、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover、external proof。
- `o1_pr5_hardware`: 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry、WAVE ROVER/UART/HIL packet material。
- `pr4_route_elevator`: Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material、delivery_result。
- `o4_real_phone`: real iPhone/Android behavior、production app、PWA prompt/user choice、true phone/browser acceptance。

Shared safe fields：

- `material_group`
- `intake_status`
- `safe_evidence_ref`
- `same_evidence_ref_required`
- `accepted_items`
- `missing_items`
- `rejected_items`
- `next_action`
- `owner_handoff`
- `evidence_boundary`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## 4. 并行 Owner 任务拆分

### 4.1 Hardware/Autonomy Owner

文件范围：

- `pc-tools/evidence/real_material_evidence_intake.py`
- `tests/test_real_material_evidence_intake.py`
- `docs/interfaces/real_material_evidence_intake.md`
- `sprints/2026.05.19_21-22_real-material-evidence-intake/evidence/real_material_evidence_intake.json`
- `sprints/2026.05.19_21-22_real-material-evidence-intake/evidence/real_material_evidence_intake_summary.json`
- `sprints/2026.05.19_21-22_real-material-evidence-intake/tech-done.md` 中 Hardware/Autonomy 段落

需要做什么：

- 新增 PC gate，读取 material manifest 或 sample manifest，按 material group 校验 required items。
- 校验 safe `evidence_ref`，拒绝空值、不安全字符、跨组不一致或伪造 success 字段。
- 输出 artifact 和 summary，明确 accepted/missing/rejected items、next action 和 owner handoff。
- docs/interfaces 记录 schema、material group、字段白名单、fail-closed 行为和 evidence boundary。
- sprint evidence artifact 必须写在本轮 sprint 的 `evidence/` 目录。

验收命令：

```bash
python3 -m unittest tests/test_real_material_evidence_intake.py
python3 pc-tools/evidence/real_material_evidence_intake.py --help
python3 pc-tools/evidence/real_material_evidence_intake.py --output sprints/2026.05.19_21-22_real-material-evidence-intake/evidence/real_material_evidence_intake.json --summary-output sprints/2026.05.19_21-22_real-material-evidence-intake/evidence/real_material_evidence_intake_summary.json
rg -n "real_material_evidence_intake|Objective 5|Objective 1|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/real_material_evidence_intake.py tests/test_real_material_evidence_intake.py docs/interfaces/real_material_evidence_intake.md sprints/2026.05.19_21-22_real-material-evidence-intake/evidence
git diff --check -- pc-tools/evidence/real_material_evidence_intake.py tests/test_real_material_evidence_intake.py docs/interfaces/real_material_evidence_intake.md sprints/2026.05.19_21-22_real-material-evidence-intake
```

### 4.2 Robot Owner

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.19_21-22_real-material-evidence-intake/tech-done.md` 中 Robot 段落

需要做什么：

- 在 operator gateway diagnostics 增加 `robot_diagnostics_real_material_evidence_intake_summary`。
- 只消费 `trashbot.real_material_evidence_intake_summary.v1` sanitized summary；缺失、schema 不匹配或 unsafe evidence_ref 时 fail closed。
- 保持 Robot diagnostics 只读，不读取原始 manifest、不暴露路径、凭证、checksum、raw JSON 或控制语义。
- docs/interfaces/operator_gateway_diagnostics.md 和 docs/interfaces/ros_contracts.md 记录新 diagnostics contract。

验收命令：

```bash
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
rg -n "robot_diagnostics_real_material_evidence_intake_summary|real_material_evidence_intake|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md sprints/2026.05.19_21-22_real-material-evidence-intake
```

### 4.3 Full-Stack Owner

文件范围：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.19_21-22_real-material-evidence-intake/tech-done.md` 中 Full-Stack 段落

需要做什么：

- 在 mobile/web 增加只读“真实材料回填入口” panel。
- 消费 `robot_diagnostics_real_material_evidence_intake_summary`、`real_material_evidence_intake_summary` 或兼容 phone-safe summary。
- 展示 intake status、material group、safe `evidence_ref`、accepted/missing/rejected items、next action、evidence boundary 和 not_proven。
- 不新增控制按钮，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 更新 fixture 和 mobile user flow 文档。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "真实材料回填入口|real_material_evidence_intake|robot_diagnostics_real_material_evidence_intake_summary|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md sprints/2026.05.19_21-22_real-material-evidence-intake
```

## 5. 集成验收命令

三个 owner 完成后，由主节点或 Product closeout 只做证据核对，不直接写产品代码：

```bash
python3 -m unittest tests/test_real_material_evidence_intake.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 -m py_compile pc-tools/evidence/real_material_evidence_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
rg -n "real_material_evidence_intake|robot_diagnostics_real_material_evidence_intake_summary|Objective 5|Objective 1|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/real_material_evidence_intake.py tests/test_real_material_evidence_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py docs/interfaces/real_material_evidence_intake.md docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.19_21-22_real-material-evidence-intake
git diff --check -- pc-tools/evidence/real_material_evidence_intake.py tests/test_real_material_evidence_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/interfaces/real_material_evidence_intake.md docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.19_21-22_real-material-evidence-intake
```

## 6. 风险和失败定位

- 若 PC gate 输出 success/pass 字段：失败，必须改为 intake status、accepted/missing/rejected 和 `not_proven`。
- 若 Robot diagnostics 读取原始 manifest：失败，必须只消费 sanitized summary。
- 若 mobile/web 因 panel 开启 primary action：失败，必须保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。
- 若文档缺少 evidence boundary：失败，必须补充 `software_proof_docker_real_material_evidence_intake_gate` 和 fail-closed 字段。
- 若工程实现需要真实硬件、真实公网或真实手机才能通过测试：失败，本轮验收只能依赖 Docker/local software proof 和 fenced unit tests。

## 7. 输出要求

每个 owner 返回：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. 失败定位，如有。
4. 剩余风险。

Product closeout 后续必须补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并在 final 中保守记录 OKR 百分比是否仍不变。
