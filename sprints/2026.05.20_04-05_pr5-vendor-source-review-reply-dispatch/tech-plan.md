# Sprint 2026.05.20_04-05 PR5 Vendor Source Review Reply Dispatch - Tech Plan

## 1. 技术方案

新增 `pr5_vendor_source_review_reply_dispatch`。它的职责不是发布 GitHub 评论，也不是证明 2D LiDAR / ToF 已经有真实材料，而是把 03-04 的 `pr5_vendor_source_review_packet` 转成可人工发布、可机器复核、默认 fail-closed 的 GitHub review reply Markdown 和 summary。

实现原则：

- 输入优先使用 `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet_summary.json`。
- 必须保留 thread id：`PRRT_kwDOSWB9286CJ3tX`。
- 必须引用本地 source boundary：`docs/vendor/VENDOR_INDEX.md` 及其指向的 WAVE ROVER / Orange Pi / UART JSON / firmware/vendor app references。
- 只能声明 local vendor tree 的 source boundary；2D LiDAR / ToF 继续声明为 `hardware_material_pending` / `not_proven`。
- 输出 Markdown reply、artifact 和 summary，供 Product 人工复核、Robot diagnostics 和 mobile/web 只读消费。
- 不访问真实硬件、串口、ROS graph、GitHub 写接口、云资源或真实手机浏览器。

目标证据边界：

- `software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate`
- `source=software_proof`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## 2. Owner / 文件范围

### hardware-engineer

主责：reply-dispatch generator、artifact schema、Markdown safety scanner 和 source-boundary semantics。

允许改动：

- `pc-tools/evidence/pr5_vendor_source_review_reply_dispatch.py`
- `tests/test_pr5_vendor_source_review_reply_dispatch.py`
- `docs/interfaces/pr5_vendor_source_review_reply_dispatch.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply_dispatch.json`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply_dispatch_summary.json`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply.md`

接口影响：

- 新增 artifact schema：`trashbot.pr5_vendor_source_review_reply_dispatch.v1`
- 新增 summary schema：`trashbot.pr5_vendor_source_review_reply_dispatch_summary.v1`
- 不新增硬件配置、不改 launch、不改 ROS2 driver、不读取串口、不调用 GitHub write API。

### robot-software-engineer

主责：metadata-only diagnostics safe alias。

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/interfaces/ros_contracts.md`

接口影响：

- 新增 safe alias：`robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary`
- Robot alias schema：`trashbot.robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary.v1`
- Alias 只读暴露 safe fields：`thread_id`、`reply_status`、`source`、`proof_boundary`、`vendor_source_boundary`、`hardware_material_pending`、`missing_materials`、`next_required_evidence`、`safe_copy`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不读取 raw Markdown body 以外的 secret/token，不读取硬件，不打开 serial/UART，不访问 ROS graph，不发 ACK/cursor/command。

### full-stack-software-engineer

主责：mobile/web 只读 panel 和 fixture。

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary.json`
- `docs/product/mobile_user_flow.md`

接口影响：

- 手机端只读展示 PR #5 vendor/source review reply-dispatch 状态。
- Start Delivery / Confirm Dropoff / Cancel 继续 disabled；不得新增控制 endpoint、ACK、cursor 或 retry side effect。
- UI copy 必须中文优先，明确 “可发布 reply 不是真实采购、真实安装、标定、HIL、真实手机验收或送达证明”。

### product-okr-owner

主责：产品验收、OKR 边界和 sprint 收口。

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/tech-done.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/side2side_check.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/final.md`

接口影响：

- Product 只记录 `software_proof` 边界，不提高 Objective 5、Objective 1 或 Objective 4。
- `PRRT_kwDOSWB9286CJ3tX` 只能写成 reply-ready / still `not_proven`，不得写成自动 resolved。
- 如果实际发布 GitHub reply，必须在 closeout 中区分 “生成 reply” 和 “已发布 reply”；本 sprint 默认只实现生成能力。

## 3. 并行启动计划

本 sprint 是 4 owner Epic，文件范围互不重叠，必须并行启动 4 个 worker：

- `hardware-engineer`：实现 reply-dispatch generator、Markdown artifact 和 focused tests。
- `robot-software-engineer`：并行实现 diagnostics alias，可先使用计划中的 summary fixture；若 Hardware schema 有字段差异，alias 层兼容。
- `full-stack-software-engineer`：并行实现 mobile fixture + panel，消费 Robot alias shape。
- `product-okr-owner`：并行准备 closeout checklist、OKR/progress wording 和 GitHub reply 安全验收项。

集成规则：

- Hardware 不扩大到 Robot 代码。
- Robot 不直接读 PC raw artifact body，只消费 sanitized summary。
- Full-Stack 不直接读 PC artifact，不新增控制副作用。
- Product 不把 reply-ready 写成 resolved，不把 `software_proof` 写成真实材料。

## 4. 验收命令

### Hardware

```bash
test -f docs/vendor/VENDOR_INDEX.md
test -f sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet_summary.json
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/pr5_vendor_source_review_reply_dispatch.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_pr5_vendor_source_review_reply_dispatch.py
python3 pc-tools/evidence/pr5_vendor_source_review_reply_dispatch.py --packet-summary sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/evidence/pr5_vendor_source_review_packet_summary.json --output sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply_dispatch.json --summary-output sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply_dispatch_summary.json --markdown-output sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply.md
rg -n "PRRT_kwDOSWB9286CJ3tX|docs/vendor/VENDOR_INDEX.md|2D LiDAR|ToF|hardware_material_pending|software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests docs/interfaces/pr5_vendor_source_review_reply_dispatch.md sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence
git diff --check -- pc-tools/evidence/pr5_vendor_source_review_reply_dispatch.py tests/test_pr5_vendor_source_review_reply_dispatch.py docs/interfaces/pr5_vendor_source_review_reply_dispatch.md sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch
```

### Robot

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate|software_proof|not_proven|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md
```

### Full-Stack

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "PRRT_kwDOSWB9286CJ3tX|pr5_vendor_source_review_reply_dispatch|robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary|software_proof|not_proven|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|真实采购|真实安装|HIL|送达证明" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary.json docs/product/mobile_user_flow.md
```

### Product / Integration

```bash
rg -n "sprint_type: epic|pr5_vendor_source_review_reply_dispatch|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate|software_proof|not_proven|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch
git diff --check -- OKR.md docs/process/okr_progress_log.md pc-tools/evidence/pr5_vendor_source_review_reply_dispatch.py tests/test_pr5_vendor_source_review_reply_dispatch.py docs/interfaces/pr5_vendor_source_review_reply_dispatch.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary.json docs/product/mobile_user_flow.md sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch
git diff --cached --check
```

### Planning-only fence for this Product task

```bash
test -f sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/pre_start.md
test -f sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/prd.md
test -f sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/tech-plan.md
rg -n "sprint_type: epic|PRRT_kwDOSWB9286CJ3tX|Objective 5|Objective 1|software_proof|not_proven|hardware_material_pending|OKR 最低优先级核对|pr5_vendor_source_review_reply_dispatch" sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch
git diff --check -- sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch
```

## 5. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接推进 Objective 5 completion；本 sprint 针对 Objective 1 / Objective 4 相关的 PR #5 vendor/source review reply-dispatch 风险。
3. 不继续 Objective 5 的理由：
   - `OKR.md` 明确 O5 只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 等外部材料时才应提高 completion。
   - 本机只有 Docker，没有真实硬件，也没有 O5 外部材料。
   - 最近 `cloud_ack_outage_replay_guard`、`cloud_pending_ack_status_guard`、`cloud_command_expiry_safety_guard` 已连续推进 O5 local/Docker ACK/status guard，均未提高 O5；继续会重复本地 metadata depth。
4. 选择 PR #5 reply-dispatch 的理由：
   - GitHub PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，review 内容直接要求为 2D LiDAR / ToF mandatory assumptions 引用 `docs/vendor/` evidence。
   - 03-04 已生成 `pr5_vendor_source_review_packet`，但还没有安全 Markdown reply / summary dispatch。
   - 本轮新增的是可发布、可审查、可 fail-closed 的 reply-dispatch 能力，不是再包装 “缺真实材料” blocker，也不宣称硬件材料到位。

## 6. 风险边界

- 本轮不证明真实 2D LiDAR / ToF source、SKU、receipt、procurement、installation、wiring、power、calibration、HIL-entry、Nav2/SLAM field pass、near-field safety pass 或 delivery result。
- 本轮不证明 Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser。
- 本轮不自动关闭 `PRRT_kwDOSWB9286CJ3tX`，只生成 review-ready / fail-closed reply-dispatch。
- 本轮不默认调用 GitHub 写接口；如后续要发布 reply，必须由明确执行者使用生成 Markdown 并在 closeout 中记录发布证据。
- 技术注释规范：新增代码的技术注释必须使用中文，且解释为什么 fail closed、为什么不能把 product target 或 reply-ready 写成真实硬件证明。
