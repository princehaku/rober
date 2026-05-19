# Sprint 2026.05.20_03-04 PR5 Vendor Source Review Packet - Tech Plan

## 1. 技术方案

新增或复用一个 fail-closed PC gate：`pr5_vendor_source_review_packet`。它的职责不是证明 2D LiDAR / ToF 已经到位，而是把 PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX` 的 vendor/source review 缺口转成可执行、可复核的 `software_proof` packet。

实现原则：

- 以 `docs/vendor/VENDOR_INDEX.md` 为 source boundary 入口。
- 读取 `docs/product/production_hardware_boundary.md` 中的 default hardware set、vendor/source attribution boundary 和 hardware baseline source alignment 语义。
- 对 WAVE ROVER / Orange Pi / UART / firmware / camera/tutorial material 只声明本地 vendor source coverage。
- 对 `2D LiDAR` / `ToF` 只声明 product target / `hardware_material_pending` / `not_proven`，除非真实 source/procurement/materials 进入并通过后续独立 review。
- 输出 artifact + summary，供 Robot diagnostics 和 mobile/web 只读消费。
- 不访问真实硬件、串口、ROS graph、GitHub 写接口、云资源或手机浏览器。

目标证据边界：

- `software_proof_docker_pr5_vendor_source_review_packet_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. Owner / 文件范围

### hardware-engineer

主责：PC gate、artifact schema、source boundary semantics 和 focused tests。

允许改动：

- `pc-tools/evidence/pr5_vendor_source_review_packet.py`
- `tests/test_pr5_vendor_source_review_packet.py`
- `docs/interfaces/pr5_vendor_source_review_packet.md`
- `docs/product/production_hardware_boundary.md`
- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet.json`
- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet_summary.json`

接口影响：

- 新增 artifact schema：`trashbot.pr5_vendor_source_review_packet.v1`
- 新增 summary schema：`trashbot.pr5_vendor_source_review_packet_summary.v1`
- 不新增硬件配置、不改 launch、不改 ROS2 driver、不读取串口。

### robot-software-engineer

主责：metadata-only diagnostics safe alias。

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/interfaces/ros_contracts.md`

接口影响：

- 新增 safe alias：`robot_diagnostics_pr5_vendor_source_review_packet_summary`
- Robot alias schema：`trashbot.robot_diagnostics_pr5_vendor_source_review_packet_summary.v1`
- Alias 只读暴露 safe fields：`thread_id`、`source`、`proof_boundary`、`vendor_source_boundary`、`missing_materials`、`next_required_evidence`、`safe_copy`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不读取 raw artifact body、不读取硬件、不打开 serial/UART、不访问 ROS graph、不发 ACK/cursor/command。

### full-stack-software-engineer

主责：mobile/web 只读 panel 和 fixture。

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_pr5_vendor_source_review_packet_summary.json`
- `docs/product/mobile_user_flow.md`

接口影响：

- 手机端只读展示 PR #5 vendor/source review packet 状态。
- Start Delivery / Confirm Dropoff / Cancel 继续 disabled；不得新增控制 endpoint、ACK、cursor 或 retry side effect。
- UI copy 必须中文优先，明确“不是真实采购/安装/标定/HIL/送达证明”。

### product-okr-owner

主责：产品验收、OKR 边界和 sprint 收口。

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/tech-done.md`
- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/side2side_check.md`
- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/final.md`

接口影响：

- Product 只记录 `software_proof` 边界，不提高 O1/O5 百分比，除非真实材料独立到位。
- `PRRT_kwDOSWB9286CJ3tX` 只能写成 review-ready / still not_proven，不得写成自动 resolved。

## 3. 并行启动计划

本 sprint 是 4 owner Epic，文件范围互不重叠，必须并行启动 4 个 worker：

- `hardware-engineer`：先实现 PC gate 和 artifact。
- `robot-software-engineer`：并行实现 diagnostics alias，可使用计划中的 summary fixture；若 Hardware schema 有字段差异，集成时调整。
- `full-stack-software-engineer`：并行实现 mobile fixture + panel，消费 Robot alias shape。
- `product-okr-owner`：并行准备 closeout checklist，等待三位 Engineer 结果后更新 OKR/progress/final。

如果 schema 集成冲突，由 `robot-software-engineer` 做 alias 层兼容，Hardware 不扩大到 Robot 代码，Full-Stack 不直接读 PC raw artifact。

## 4. 验收命令

### Hardware

```bash
test -f docs/vendor/VENDOR_INDEX.md
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/pr5_vendor_source_review_packet.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_pr5_vendor_source_review_packet.py
python3 pc-tools/evidence/pr5_vendor_source_review_packet.py --output sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet.json --summary-output sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet_summary.json
rg -n "PRRT_kwDOSWB9286CJ3tX|docs/vendor/VENDOR_INDEX.md|2D LiDAR|ToF|hardware_material_pending|software_proof_docker_pr5_vendor_source_review_packet_gate|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests docs/interfaces/pr5_vendor_source_review_packet.md docs/product/production_hardware_boundary.md sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence
git diff --check -- pc-tools/evidence/pr5_vendor_source_review_packet.py tests/test_pr5_vendor_source_review_packet.py docs/interfaces/pr5_vendor_source_review_packet.md docs/product/production_hardware_boundary.md sprints/2026.05.20_03-04_pr5-vendor-source-review-packet
```

### Robot

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_pr5_vendor_source_review_packet_summary|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_pr5_vendor_source_review_packet_gate|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md
```

### Full-Stack

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "PRRT_kwDOSWB9286CJ3tX|pr5_vendor_source_review_packet|robot_diagnostics_pr5_vendor_source_review_packet_summary|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|真实采购|真实安装|HIL|送达证明" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_pr5_vendor_source_review_packet_summary.json docs/product/mobile_user_flow.md
```

### Product / Integration

```bash
rg -n "sprint_type: epic|pr5_vendor_source_review_packet|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_pr5_vendor_source_review_packet_gate|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_03-04_pr5-vendor-source-review-packet
git diff --check -- OKR.md docs/process/okr_progress_log.md pc-tools/evidence/pr5_vendor_source_review_packet.py tests/test_pr5_vendor_source_review_packet.py docs/interfaces/pr5_vendor_source_review_packet.md docs/product/production_hardware_boundary.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_pr5_vendor_source_review_packet_summary.json docs/product/mobile_user_flow.md sprints/2026.05.20_03-04_pr5-vendor-source-review-packet
git diff --cached --check
```

## 5. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5，而是针对 Objective 1 / Objective 4 的 PR #5 vendor/source review 风险。
3. 不继续 Objective 5 的理由：
   - `OKR.md` 6 明确只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 等外部材料到位才继续提高 O5。
   - 本机没有真实硬件，只有 Docker，也没有 O5 外部材料。
   - 最近 `cloud_ack_outage_replay_guard`、`cloud_pending_ack_status_guard`、`cloud_command_expiry_safety_guard` 已连续推进 O5 local/Docker ACK/status guard，均未提高 O5；继续会重复本地 metadata depth。
4. 选择 PR #5 / Objective 1 / Objective 4 的理由：
   - GitHub PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，review 内容直接要求 2D LiDAR / ToF mandatory assumptions 引用 `docs/vendor/` evidence。
   - 19-16 closeout 已把 X 判为 `blocked_pending_real_materials`，23-24 follow-up escalation status 已完成，不应继续堆“缺材料” wrapper。
   - 本轮选择的 `pr5_vendor_source_review_packet` 是新软件风险控制：它让 source boundary、missing materials、next evidence 和 safe copy 可机器复核，可为后续真实材料回填或 review response 服务。

## 6. 风险边界

- 本轮不证明真实 2D LiDAR / ToF source、SKU、receipt、procurement、installation、wiring、power、calibration、HIL-entry、Nav2/SLAM field pass、near-field safety pass 或 delivery result。
- 本轮不证明 Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser。
- 本轮不自动关闭 `PRRT_kwDOSWB9286CJ3tX`，只生成 review-ready / fail-closed packet。
- 如果 worker 发现现有 `hardware_baseline_source_alignment` 已完全覆盖目标，应复用并补齐 thread-specific review packet 输出，避免重复 gate。
- 技术注释规范：新增代码的技术注释必须使用中文，且解释为什么 fail closed、为什么不能把 product target 写成真实硬件证明。
