# Sprint 2026.05.18_22-23 Mobile Real Device Acceptance Review Handoff - PRD

## 1. 背景

上一轮 `mobile_real_device_field_trial_acceptance_review_decision*` 已经把真机现场验收会话材料转成 fail-closed review decision。当前缺口是：复核结论还没有被整理为 owner / 现场执行者可以直接使用的 handoff packet，导致下一次真实 iPhone/Android、production app 或真实 PWA prompt/user choice 材料回填时，容易再次混淆 review decision、handoff、真实验收通过和 O5 external proof。

本轮需要继续 Objective 4，但必须保持所有控制动作 fail-closed，不把 handoff packet 写成真实手机通过、真实送达、dropoff/cancel completion、HIL 或 production cloud proof。

## 2. 用户价值和产品北极星

北极星：让不会电脑和硬件的普通手机用户最终能用手机安全完成送垃圾任务，并在失败时知道谁需要补什么证据。

本轮用户价值：

- 对现场 owner：拿到一份可执行的 `mobile_real_device_field_trial_acceptance_review_handoff*` packet，知道下一次真实手机验收要补哪些材料。
- 对支持人员：在手机 UI / diagnostics 中看到同一 safe `evidence_ref`、缺口、owner handoff、next required evidence 和 safe copy。
- 对产品验收：继续把 `not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 固化在前端和 Robot diagnostics，避免把软件 proof 误写成真实手机验收。

## 3. OKR 映射

### Objective 4

- KR1：手机端最小流程继续保持 fail-closed，handoff 只解释下一步现场验收材料。
- KR5：用户验收标准继续推进，明确普通用户不接触命令行、ROS2、串口或硬件调试。
- KR7：手机 UI 美观且能直接使用；本轮新增只读 handoff panel，必须适配当前 `mobile/web` 的 first-screen support / diagnostics surface。

### 不上调的 Objective

- Objective 5：仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实 external proof。
- Objective 1：仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 和 PR #5 2D LiDAR / ToF 实物材料。
- Objective 2 / 3 / PR #4：真实 route/elevator field-material blocker 已连续消费；本轮不再继续第三次本地 wrapper。

## 4. KR 拆解或更新

本轮不直接修改 `OKR.md` 数字目标，执行完成后只允许 Product closeout 基于证据保守更新说明。建议 KR 拆解：

1. Full-stack 新增 `mobile_real_device_field_trial_acceptance_review_handoff` 只读 UI 和 fixture 消费。
2. Robot diagnostics 新增 metadata-only safe alias，允许 `/api/diagnostics` 或 compatible summary 暴露 handoff summary。
3. Product closeout 把 handoff 证据边界写入 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，并明确不证明真实手机验收。

## 5. 本轮核心抓手

把 review decision 的 `accepted/missing/rejected material summaries`、`owner_handoff`、`next_required_evidence`、`rerun_commands` 和 `safe_copy` 包装成 handoff packet。handoff 必须可复制给现场 owner，但只能包含白名单字段，不能包含 raw artifacts、local paths、checksums、tracebacks、credentials、ROS topics、`/cmd_vel`、serial/UART details、DB/queue URLs 或 OSS AK/SK。

## 6. 需要做什么

### Full-stack

- 在 `mobile/web/app.js` 新增只读 handoff panel。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`，提供 fail-closed fixture。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`，覆盖字段渲染、safe copy、缺 summary 默认 `not_proven`、primary action gating 不变。
- 更新 `docs/product/mobile_user_flow.md`，写清 evidence boundary 和不证明事项。

### Robot

- 在 `operator_gateway_diagnostics.py` 增加 diagnostics metadata-only safe alias。
- 更新 `test_operator_gateway_diagnostics.py` 覆盖 summary 透出、默认 fail-closed、安全字段白名单。
- 更新 `docs/interfaces/ros_contracts.md` 或相关接口文档，说明该 alias 不改变 ROS2 控制链路。

### Product

- 执行完成后更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 若工程证据完整，再保守更新 `OKR.md` 与 `docs/process/okr_progress_log.md`；不得把 O4 升为真实手机验收完成。

## 7. 优先级和验收口径

优先级 P0：

- Handoff summary 出现在 mobile/web 和 Robot diagnostics 的安全白名单路径。
- `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 在 fixture、UI copy、diagnostics summary 和 docs 中一致。
- Start Delivery、Confirm Dropoff、Cancel gating 完全不变。

优先级 P1：

- `safe_copy` 缺失时显示 `blocked copy unavailable` 或等价 fail-closed 文案。
- `evidence_ref` 不安全或不一致时不展示为可执行成功，只展示补证据要求。

验收口径：

- 通过 `node --check mobile/web/app.js`。
- 通过 `python3 -m unittest mobile.web.test_mobile_web_entrypoint`。
- 通过 Robot diagnostics targeted unittest。
- 通过 required `rg` 和 scoped `git diff --check`。
- sprint closeout 必须明确 `not_proven`，不证明真实 iPhone/Android、production app、真实 PWA prompt/user choice、delivery success、O5 external proof、HIL 或 route/elevator field pass。

## 8. 风险、阻塞和证据链

- 真实手机材料仍缺：真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- O5 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- O1/HIL 仍缺：WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report。
- PR #5 仍缺：2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 真实材料。
- PR #4 仍缺：真实 route/elevator field pass、门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 或 delivery result。
