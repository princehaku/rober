# Sprint 2026.05.19_23-24 Real Material Followup Escalation Status - Tech Plan

## 1. Sprint 类型和实现原则

- sprint_type: epic
- 本轮目标是规划 `real_material_followup_escalation_status`，把 manifest template / evidence intake 后的真实材料缺口转成可追责、可重跑、可升级的状态功能。
- 当前环境只有 Docker。不得把 follow-up status、Robot diagnostics、mobile/web panel、本地测试或 rerun command summary 写成真实材料通过。
- 后续实现必须按 2-4 个 owner 并行推进；本轮规划文档完成后，默认进入实现阶段，由子 agent 执行代码、测试、修复和文档同步。
- 所有新增代码技术注释必须使用中文，且解释为什么 fail closed、为什么过滤敏感字段、为什么不能把 follow-up status 当成真实通过。
- 证据边界固定为 `software_proof_docker_real_material_followup_escalation_status_gate`，并保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 里完成度最低的是 Objective 5，约 68%。下一低项是 Objective 1，约 81%。Objective 2 / Objective 3 / Objective 4 均约 99%。
2. 本 sprint 直接针对 Objective 5 的真实 external proof 缺口，同时覆盖 Objective 1 / PR #5 hardware、PR #4 route/elevator 和 Objective 4 real phone 的真实材料 follow-up。
3. 选择 `real-material-followup-escalation-status` 的理由：
   - Objective 5 数字最低，但 Docker-only 主机无法产生真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover 或真实 external proof。
   - Objective 1 次低，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，真实 2D LiDAR / ToF、`docs/vendor/` source citation、WAVE ROVER/UART/HIL 材料仍未到位。
   - `20-21_real-material-readiness-board`、`21-22_real-material-evidence-intake`、`22-23_real-material-manifest-template` 已完成 readiness / intake / template 三段；继续堆本地 proof 会重复消费同一 blocker。
   - 最新 final 明确下一轮若仍无真实材料，应升级现场材料提供请求。本轮的 escalation status 正是把“谁该补什么、是否逾期、升级到哪一级、该重跑什么命令”产品化。

## 3. 接口和证据合同

后续新增 contract 建议：

- artifact schema：`trashbot.real_material_followup_escalation_status.v1`
- summary schema：`trashbot.real_material_followup_escalation_status_summary.v1`
- Robot safe alias：`robot_diagnostics_real_material_followup_escalation_status_summary`
- source compatibility：`real_material_manifest_template`、`real_material_evidence_intake`
- evidence boundary：`software_proof_docker_real_material_followup_escalation_status_gate`

Material groups：

- `o5_external`：HTTPS/TLS public ingress、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover、external proof。
- `o1_pr5_hardware`：2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry、WAVE ROVER/UART/HIL packet material、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、operator HIL report。
- `pr4_route_elevator`：Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material、delivery_result。
- `o4_real_phone`：real iPhone/Android behavior、production app、PWA prompt/user choice、true phone/browser acceptance。

Shared safe fields：

- `material_group`
- `safe_evidence_ref`
- `field_owner`
- `due_status`
- `blocked_reason`
- `next_required_evidence`
- `escalation_level`
- `rerun_command`
- `rerun_status_summary`
- `source_template_status`
- `source_intake_status`
- `review_route`
- `owner_handoff`
- `evidence_boundary`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Rejected material classes：

- credentials、bearer tokens、OSS AK/SK、root password
- absolute local paths or private host paths
- raw ROS topic dumps that expose control internals
- raw serial/UART control commands
- full private logs、raw artifacts、checksums、DB/queue URLs
- any `pass`、`success`、`delivery_success=true`、`primary_actions_enabled=true`、`safe_to_control=true` claim

## 4. 并行 Owner 任务拆分

### 4.1 Hardware Infra Owner

文件范围：

- `pc-tools/evidence/real_material_followup_escalation_status.py`
- `tests/test_real_material_followup_escalation_status.py`
- `docs/interfaces/real_material_followup_escalation_status.md`
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status.json`
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status_summary.json`
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/tech-done.md` 中 Hardware 段落

需要做什么：

- 新增 PC gate / artifact generator，输出四类 material group 的 follow-up escalation status。
- O1 / PR #5 hardware 字段必须引用 `docs/vendor/VENDOR_INDEX.md` 作为硬件事实入口；不得写死未验证的引脚、电压、UART 设备名、传感器 source 或机械尺寸。
- `PRRT_kwDOSWB9286CJ3tX` 必须输出 `blocked_pending_real_materials`，并要求 mandatory sensor baseline cite `docs/vendor/` sources。
- 输出 owner、due_status、blocked_reason、next_required_evidence、escalation_level、rerun command/status summary。

验收命令：

```bash
test -f docs/vendor/VENDOR_INDEX.md
python3 -m unittest tests/test_real_material_followup_escalation_status.py
python3 pc-tools/evidence/real_material_followup_escalation_status.py --help
python3 pc-tools/evidence/real_material_followup_escalation_status.py --output sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status.json --summary-output sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status_summary.json
rg -n "real_material_followup_escalation_status|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|blocked_pending_real_materials|docs/vendor/VENDOR_INDEX.md|due_status|blocked_reason|next_required_evidence|escalation_level|software_proof_docker_real_material_followup_escalation_status_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/real_material_followup_escalation_status.py tests/test_real_material_followup_escalation_status.py docs/interfaces/real_material_followup_escalation_status.md sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence
git diff --check -- pc-tools/evidence/real_material_followup_escalation_status.py tests/test_real_material_followup_escalation_status.py docs/interfaces/real_material_followup_escalation_status.md sprints/2026.05.19_23-24_real-material-followup-escalation-status
```

### 4.2 Autonomy Owner

文件范围：

- `pc-tools/evidence/real_material_followup_escalation_status.py` 中 `pr4_route_elevator` 数据段或配置段
- `tests/test_real_material_followup_escalation_status.py` 中 route/elevator coverage
- `docs/interfaces/real_material_followup_escalation_status.md` 中 PR #4 route/elevator section
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/tech-done.md` 中 Autonomy 段落

需要做什么：

- 为 `pr4_route_elevator` 输出真实 Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material、delivery_result 的 follow-up status。
- 保持同一 safe `evidence_ref`，不得把 field checklist、due_status 或 rerun status 写成真实 route/elevator field pass。
- 与 Hardware owner 共享 PC gate 文件时，由 Hardware owner 主责集成，Autonomy 只提交清晰数据段或测试补丁，避免覆盖他人改动。

验收命令：

```bash
python3 -m unittest tests/test_real_material_followup_escalation_status.py
rg -n "pr4_route_elevator|Nav2|fixed-route|route completion signal|field task record|elevator door state|target floor confirmation|human assistance record|delivery_result|due_status|blocked_reason|next_required_evidence|escalation_level|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/real_material_followup_escalation_status.py tests/test_real_material_followup_escalation_status.py docs/interfaces/real_material_followup_escalation_status.md
git diff --check -- pc-tools/evidence/real_material_followup_escalation_status.py tests/test_real_material_followup_escalation_status.py docs/interfaces/real_material_followup_escalation_status.md sprints/2026.05.19_23-24_real-material-followup-escalation-status
```

### 4.3 Robot Platform Owner

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/tech-done.md` 中 Robot 段落

需要做什么：

- 增加 `robot_diagnostics_real_material_followup_escalation_status_summary` safe alias。
- 只消费 sanitized summary；缺 summary、schema mismatch、unsafe `evidence_ref`、raw manifest、raw materials、credential、checksum、success/control 字段时 fail closed。
- 不改变 robot command path，不增加 Start/Confirm/Cancel 或任何运动授权。

验收命令：

```bash
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
rg -n "robot_diagnostics_real_material_followup_escalation_status_summary|real_material_followup_escalation_status|due_status|blocked_reason|next_required_evidence|escalation_level|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md sprints/2026.05.19_23-24_real-material-followup-escalation-status
```

### 4.4 Full-Stack Owner

文件范围：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/tech-done.md` 中 Full-Stack 段落

需要做什么：

- 增加只读 “真实材料升级状态” panel。
- 消费 `robot_diagnostics_real_material_followup_escalation_status_summary`、`real_material_followup_escalation_status_summary` 或兼容 phone-safe summary。
- 展示 material groups、safe `evidence_ref`、field owner、due_status、blocked_reason、next_required_evidence、escalation_level、rerun command/status summary、boundary 和 `not_proven`。
- 不新增控制按钮，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 更新 mobile fixture 和 `docs/product/mobile_user_flow.md`，明确它不是真实手机/browser proof。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "真实材料升级状态|real_material_followup_escalation_status|robot_diagnostics_real_material_followup_escalation_status_summary|due_status|blocked_reason|next_required_evidence|escalation_level|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md sprints/2026.05.19_23-24_real-material-followup-escalation-status
```

## 5. 集成验收命令

所有 owner 完成后，由 Product closeout / 主节点只做证据核对和 sprint 留档，不直接写产品代码：

```bash
python3 -m unittest tests/test_real_material_followup_escalation_status.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 -m py_compile pc-tools/evidence/real_material_followup_escalation_status.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
rg -n "real_material_followup_escalation_status|robot_diagnostics_real_material_followup_escalation_status_summary|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|blocked_pending_real_materials|due_status|blocked_reason|next_required_evidence|escalation_level|software_proof_docker_real_material_followup_escalation_status_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/real_material_followup_escalation_status.py tests/test_real_material_followup_escalation_status.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py docs/interfaces/real_material_followup_escalation_status.md docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.19_23-24_real-material-followup-escalation-status
git diff --check -- pc-tools/evidence/real_material_followup_escalation_status.py tests/test_real_material_followup_escalation_status.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/interfaces/real_material_followup_escalation_status.md docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.19_23-24_real-material-followup-escalation-status
```

## 6. 本轮规划文档验收命令

本轮 Product Owner 只创建规划三文档，验收命令为：

```bash
test -f sprints/2026.05.19_23-24_real-material-followup-escalation-status/pre_start.md && test -f sprints/2026.05.19_23-24_real-material-followup-escalation-status/prd.md && test -f sprints/2026.05.19_23-24_real-material-followup-escalation-status/tech-plan.md
rg -n "sprint_type: epic|real_material_followup_escalation_status|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|blocked_pending_real_materials|software_proof_docker_real_material_followup_escalation_status_gate|OKR 最低优先级核对|Robot|Full-Stack|Hardware|Autonomy" sprints/2026.05.19_23-24_real-material-followup-escalation-status
git diff --check -- sprints/2026.05.19_23-24_real-material-followup-escalation-status
```

## 7. 风险和失败定位

- 若 implementation 输出 success/pass 或把 follow-up status 写成真实 material proof：失败，退回 `not_proven`。
- 若 O5 status 不要求真实 external materials：失败，补齐 HTTPS/TLS、4G/SIM、OSS/CDN、DB/queue、worker/cutover。
- 若 O1 / PR #5 status 没有覆盖 `PRRT_kwDOSWB9286CJ3tX`、`blocked_pending_real_materials`、`docs/vendor/` source citation 和真实 2D LiDAR / ToF / WAVE ROVER/HIL 材料：失败。
- 若 PR #4 route/elevator status 缺 route/elevator field materials 或把 due_status 写成 route/elevator field pass：失败。
- 若 O4 status 被写成真实手机/browser proof：失败，必须回到 `software_proof`。
- 若 Robot 或 mobile 消费 raw manifest、raw materials、凭证、绝对路径、raw control 或 checksum：失败，必须只消费 sanitized summary。
- 若任何实现需要真实硬件、真实公网或真实手机才能通过本地验收：失败，本 sprint 的本地验收只允许 Docker/local fenced proof。

## 8. 输出要求

每个 owner 返回：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. 失败定位，如有。
4. 剩余风险。

Product closeout 后续必须补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并按真实交付情况保守更新 `OKR.md`。没有真实材料前，Objective 5、Objective 1、PR #5、PR #4 route/elevator 和 Objective 4 不得提升为真实完成。
