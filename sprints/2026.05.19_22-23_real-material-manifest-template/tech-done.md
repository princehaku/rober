# Sprint 2026.05.19_22-23 Real Material Manifest Template - Tech Done

## 1. Sprint 类型和交付结论

- sprint_type: epic
- 本轮工程 owner 已完成 `real_material_evidence_intake` 兼容的 `real_material_manifest_template` / field-owner submission pack。
- 证据边界：`software_proof_docker_real_material_manifest_template_gate`，兼容 `real_material_evidence_intake` 的 software-proof manifest-template boundary。
- 本轮不证明真实材料、HIL、external proof、real phone/browser、route/elevator field pass 或 delivery success。
- Fail-closed 状态保持：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 2. 实际改动

### Hardware / Autonomy

- `real_material_evidence_intake` 增加 `real_material_manifest_template` 能力，输出 field-owner 可填写的 material template group。
- 增加 template CLI、tests、docs、README 和 sprint evidence artifact：`sprints/2026.05.19_22-23_real-material-manifest-template/evidence/real_material_manifest_template.json`。
- Template groups 覆盖：
  - `o5_external`
  - `o1_pr5_hardware`
  - `pr4_route_elevator`
  - `o4_real_phone`
- O1 / PR #5 hardware template 保留 `docs/vendor/VENDOR_INDEX.md` 作为硬件事实入口；本轮没有新增引脚、电压、UART 设备名、波特率、速度映射、反馈协议或机械尺寸假设。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍保持 unresolved / `blocked_pending_real_materials`，不得因 template 生成而关闭。

### Robot Platform

- Diagnostics 增加 `real_material_manifest_template` safe alias。
- Robot safe summary 兼容 `manifest_template`、`template_groups`、`required_item_templates`。
- Robot 消费仍为只读 diagnostics summary；不读取 raw manifest，不暴露凭证、绝对路径、raw control、checksum 或 success/control 字段。
- Start Delivery、Confirm Dropoff、Cancel 和任何运动控制授权均未改变。

### Full-Stack

- mobile/web 增加只读“真实材料回填入口”展示 manifest template groups。
- 页面展示 material group、safe evidence ref、owner handoff、next required evidence 和 fail-closed boundary。
- Start Delivery、Confirm Dropoff、Cancel gating 不变；本轮不是 real phone/browser proof。

## 3. 验证结果

Engineering owner 已报告：

- Hardware / Autonomy：`python3 -m unittest tests/test_real_material_evidence_intake.py` 输出 `Ran 7 tests ... OK`。
- Hardware / Autonomy：`py_compile`、template CLI、required `rg`、scoped `git diff --check` 通过。
- Robot：`python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 215 tests ... OK`。
- Robot：`py_compile`、required `rg`、scoped `git diff --check` 通过。
- Full-Stack：`python3 mobile/web/test_mobile_web_entrypoint.py` 输出 `Ran 139 tests ... OK`。
- Full-Stack：`node --check mobile/web/app.js`、required `rg`、scoped `git diff --check` 通过。

Product closeout 复跑验收命令，结果记录在 `final.md`。

## 4. 偏差和范围控制

- `tech-plan.md` 规划曾建议独立 `real_material_manifest_template.py` / summary artifact；工程实际选择在 `real_material_evidence_intake` 内兼容实现，并提供 `real_material_manifest_template` artifact。该偏差可接受，因为本轮目标是让 field-owner template 与 intake 语义兼容。
- 本轮 engineering 改动和 Product closeout 由主会话在最终验收后统一提交并推送。
- 本轮不改工程代码、tests、mobile、onboard、pc-tools 或 evidence artifact；Product closeout 只更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 5. 剩余风险

- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover。
- Objective 1 仍缺真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report、真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- PR #4 route/elevator 仍缺真实 Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material 和 delivery_result。
- Objective 4 仍缺真实 iPhone/Android device behavior、production app、PWA prompt/user choice 和 true phone/browser acceptance。
- `real_material_manifest_template` 只能作为真实材料采集模板和后续 intake/review 的 software-proof 入口，不得写成真实材料通过。
