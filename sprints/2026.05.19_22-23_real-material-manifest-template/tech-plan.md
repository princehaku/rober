# Sprint 2026.05.19_22-23 Real Material Manifest Template - Tech Plan

## 1. Sprint 类型和实现原则

- sprint_type: epic
- 本轮目标是规划 field-owner `manifest template` / submission pack，让真实材料到位时能进入上一轮 `real_material_evidence_intake` 后续链路。
- 当前环境只有 Docker。不得把模板、sample submission、diagnostics summary、mobile/web panel 或本地测试写成真实材料通过。
- 后续实现必须按 2-4 个 owner 并行推进；本轮规划文档完成后，默认进入实现阶段，由子 agent 执行代码、测试、修复和文档同步。
- 所有新增代码技术注释必须使用中文，且解释为什么 fail closed、为什么过滤敏感字段、为什么不能把 manifest template 当成真实通过。
- 证据边界固定为 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 里完成度最低的是 Objective 5，约 68%。下一低项是 Objective 1，约 81%。
2. 本 sprint 直接针对 Objective 5 的真实 external proof 缺口，同时覆盖 Objective 1 / PR #5 hardware、PR #4 route/elevator 和 Objective 4 real phone 的真实材料提交模板。
3. 选择 `real-material-manifest-template` 的理由：
   - Objective 5 数字最低，但 Docker-only 主机无法产生真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover 或真实 external proof。
   - Objective 1 次低，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，真实 2D LiDAR / ToF 和 WAVE ROVER/UART/HIL 材料仍未到位。
   - 最新 `2026.05.19_20-21_real-material-readiness-board/final.md` 和 `2026.05.19_21-22_real-material-evidence-intake/final.md` 已明确不能再重复 local metadata wrapper。
   - 本轮把上一轮 intake 的隐式 sample manifest 变成 field-owner 可交付 `manifest template`，是让真实材料回填变得可执行的下一步，而不是重复 blocked proof。

## 3. 接口和证据合同

后续新增 contract 建议：

- artifact schema：`trashbot.real_material_manifest_template.v1`
- summary schema：`trashbot.real_material_manifest_template_summary.v1`
- source intake compatibility：`real_material_evidence_intake`
- evidence boundary：`software_proof_docker_real_material_manifest_template_gate`
- required fail-closed fields：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`

Material groups：

- `o5_external`：HTTPS/TLS public ingress、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover、external proof。
- `o1_pr5_hardware`：2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry、WAVE ROVER/UART/HIL packet material、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、operator HIL report。
- `pr4_route_elevator`：Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material、delivery_result。
- `o4_real_phone`：real iPhone/Android behavior、production app、PWA prompt/user choice、true phone/browser acceptance。

Shared safe fields：

- `material_group`
- `safe_evidence_ref`
- `same_evidence_ref_required=true`
- `field_owner`
- `required_materials`
- `optional_materials`
- `rejected_materials`
- `submission_instructions`
- `review_route`
- `owner_handoff`
- `next_required_evidence`
- `evidence_boundary`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Rejected material classes：

- credentials, bearer tokens, OSS AK/SK, root password
- absolute local paths or private host paths
- raw ROS topic dumps that expose control internals
- raw serial/UART control commands
- full private logs, raw artifacts, checksums, DB/queue URLs
- any `pass`、`success`、`delivery_success=true`、`primary_actions_enabled=true`、`safe_to_control=true` claim

## 4. 并行 Owner 任务拆分

### 4.1 Hardware Infra Owner

文件范围：

- `pc-tools/evidence/real_material_manifest_template.py`
- `tests/test_real_material_manifest_template.py`
- `docs/interfaces/real_material_manifest_template.md`
- `sprints/2026.05.19_22-23_real-material-manifest-template/evidence/real_material_manifest_template.json`
- `sprints/2026.05.19_22-23_real-material-manifest-template/evidence/real_material_manifest_template_summary.json`
- `sprints/2026.05.19_22-23_real-material-manifest-template/tech-done.md` 中 Hardware 段落

需要做什么：

- 新增 PC gate / artifact generator，输出四类 material group 的 `manifest template`。
- O1 / PR #5 hardware 字段必须引用 `docs/vendor/VENDOR_INDEX.md` 作为硬件事实入口；不得写死未验证的引脚、电压、UART 设备名或机械尺寸。
- 每个 group 都要求同一 safe `evidence_ref`，并明确 sample submission 是 `not_proven`。
- 拒绝凭证、绝对路径、raw control、success/control 字段。

验收命令：

```bash
python3 -m unittest tests/test_real_material_manifest_template.py
python3 pc-tools/evidence/real_material_manifest_template.py --help
python3 pc-tools/evidence/real_material_manifest_template.py --output sprints/2026.05.19_22-23_real-material-manifest-template/evidence/real_material_manifest_template.json --summary-output sprints/2026.05.19_22-23_real-material-manifest-template/evidence/real_material_manifest_template_summary.json
rg -n "real_material_manifest_template|manifest template|Objective 5|Objective 1|PR #5|PRRT_kwDOSWB9286CJ3tX|docs/vendor/VENDOR_INDEX.md|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/real_material_manifest_template.py tests/test_real_material_manifest_template.py docs/interfaces/real_material_manifest_template.md sprints/2026.05.19_22-23_real-material-manifest-template/evidence
git diff --check -- pc-tools/evidence/real_material_manifest_template.py tests/test_real_material_manifest_template.py docs/interfaces/real_material_manifest_template.md sprints/2026.05.19_22-23_real-material-manifest-template
```

### 4.2 Autonomy Owner

文件范围：

- `pc-tools/evidence/real_material_manifest_template.py` 中 `pr4_route_elevator` 数据段或配置段
- `tests/test_real_material_manifest_template.py` 中 route/elevator coverage
- `docs/interfaces/real_material_manifest_template.md` 中 PR #4 route/elevator section
- `sprints/2026.05.19_22-23_real-material-manifest-template/tech-done.md` 中 Autonomy 段落

需要做什么：

- 只补 `pr4_route_elevator` 材料清单事实：Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material、delivery_result。
- 保持同一 safe `evidence_ref`，不得把 field checklist 写成真实 route/elevator field pass。
- 与 Hardware owner 共享 PC gate 文件时，由 Hardware owner 主责集成，Autonomy 只提交清晰数据段或测试补丁，避免覆盖他人改动。

验收命令：

```bash
python3 -m unittest tests/test_real_material_manifest_template.py
rg -n "pr4_route_elevator|Nav2|fixed-route|route completion signal|field task record|elevator door state|target floor confirmation|human assistance record|delivery_result|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/real_material_manifest_template.py tests/test_real_material_manifest_template.py docs/interfaces/real_material_manifest_template.md
git diff --check -- pc-tools/evidence/real_material_manifest_template.py tests/test_real_material_manifest_template.py docs/interfaces/real_material_manifest_template.md sprints/2026.05.19_22-23_real-material-manifest-template
```

### 4.3 Robot Platform Owner

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.19_22-23_real-material-manifest-template/tech-done.md` 中 Robot 段落

需要做什么：

- 增加 `robot_diagnostics_real_material_manifest_template_summary` safe alias。
- 只消费 sanitized summary；缺 summary、schema mismatch、unsafe `evidence_ref`、raw manifest、credential、checksum、success/control 字段时 fail closed。
- 不改变 robot command path，不增加 Start/Confirm/Cancel 或任何运动授权。

验收命令：

```bash
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
rg -n "robot_diagnostics_real_material_manifest_template_summary|real_material_manifest_template|manifest template|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md sprints/2026.05.19_22-23_real-material-manifest-template
```

### 4.4 Full-Stack Owner

文件范围：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.19_22-23_real-material-manifest-template/tech-done.md` 中 Full-Stack 段落

需要做什么：

- 增加只读 “真实材料提交模板” / field-owner submission pack panel。
- 消费 `robot_diagnostics_real_material_manifest_template_summary`、`real_material_manifest_template_summary` 或兼容 phone-safe summary。
- 展示 material groups、safe `evidence_ref`、owner handoff、next required evidence、boundary 和 `not_proven`。
- 不新增控制按钮，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 更新 mobile fixture 和 `docs/product/mobile_user_flow.md`，明确它不是真实手机/browser proof。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "真实材料提交模板|real_material_manifest_template|robot_diagnostics_real_material_manifest_template_summary|manifest template|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md sprints/2026.05.19_22-23_real-material-manifest-template
```

## 5. 集成验收命令

所有 owner 完成后，由 Product closeout / 主节点只做证据核对和 sprint 留档，不直接写产品代码：

```bash
python3 -m unittest tests/test_real_material_manifest_template.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 -m py_compile pc-tools/evidence/real_material_manifest_template.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
rg -n "real_material_manifest_template|robot_diagnostics_real_material_manifest_template_summary|manifest template|Objective 5|Objective 1|PR #5|PRRT_kwDOSWB9286CJ3tX|real_material_evidence_intake|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/real_material_manifest_template.py tests/test_real_material_manifest_template.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py docs/interfaces/real_material_manifest_template.md docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.19_22-23_real-material-manifest-template
git diff --check -- pc-tools/evidence/real_material_manifest_template.py tests/test_real_material_manifest_template.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/interfaces/real_material_manifest_template.md docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.19_22-23_real-material-manifest-template
```

## 6. 本轮规划文档验收命令

本轮 Product Owner 只创建规划三文档，验收命令为：

```bash
test -f sprints/2026.05.19_22-23_real-material-manifest-template/pre_start.md && test -f sprints/2026.05.19_22-23_real-material-manifest-template/prd.md && test -f sprints/2026.05.19_22-23_real-material-manifest-template/tech-plan.md
rg -n "sprint_type: epic|Objective 5|Objective 1|PR #5|PRRT_kwDOSWB9286CJ3tX|real_material_evidence_intake|manifest template|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|OKR 最低优先级核对" sprints/2026.05.19_22-23_real-material-manifest-template
git diff --check -- sprints/2026.05.19_22-23_real-material-manifest-template
```

## 7. 风险和失败定位

- 若 implementation 输出 success/pass 或把 template 写成真实 material proof：失败，退回 `not_proven`。
- 若 O5 template 不要求真实 external materials：失败，补齐 HTTPS/TLS、4G/SIM、OSS/CDN、DB/queue、worker/cutover。
- 若 O1 / PR #5 template 没有覆盖 `PRRT_kwDOSWB9286CJ3tX` 和真实 2D LiDAR / ToF / WAVE ROVER/HIL 材料：失败。
- 若 PR #4 route/elevator template 没有同一 safe `evidence_ref` 或缺 route/elevator field materials：失败。
- 若 O4 template 被写成真实手机/browser proof：失败，必须回到 `software_proof`。
- 若 Robot 或 mobile 消费 raw manifest、凭证、绝对路径、raw control 或 checksum：失败，必须只消费 sanitized summary。
- 若任何实现需要真实硬件、真实公网或真实手机才能通过本地验收：失败，本 sprint 的本地验收只允许 Docker/local fenced proof。

## 8. 输出要求

每个 owner 返回：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. 失败定位，如有。
4. 剩余风险。

Product closeout 后续必须补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并按真实交付情况保守更新 `OKR.md`。没有真实材料前，Objective 5、Objective 1、PR #5、PR #4 route/elevator 和 Objective 4 不得提升为真实完成。
