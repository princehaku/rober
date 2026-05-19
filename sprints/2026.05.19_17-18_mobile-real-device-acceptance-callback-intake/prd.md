# Sprint 2026.05.19_17-18 Mobile Real Device Acceptance Callback Intake - PRD

## 1. 用户价值和产品北极星

北极星：普通手机用户不接触命令行、ROS2、串口、云凭证或硬件调试，也能完成一次送垃圾任务，理解当前状态，并在失败时知道谁接手、补什么证据、如何 rerun。

本轮用户价值不是让手机验收“看起来完成”，而是让真实手机执行后的回调材料可以被安全接收和分流。现场 owner 后续拿着上一轮 `mobile_real_device_field_trial_acceptance_execution_pack*` 到真实 iPhone/Android、production app 或 PWA prompt/user choice 场景执行后，可以把结果回填为 accepted、missing 或 rejected callback evidence；系统必须继续给出 same safe `evidence_ref`、owner handoff、`next_required_evidence` 和 rerun guidance。

## 2. OKR 映射

- Objective 4：本轮主目标。补齐真实手机验收 execution pack 的 callback intake 入口，服务 KR1、KR5、KR7，让现场手机验收材料具备结构化回流和 fail-closed 复核路径。
- Objective 5：不推进 completion。真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external phone/browser proof 仍缺。
- Objective 1：不推进 completion。真实 WAVE ROVER/UART/HIL、底盘 feedback、operator HIL report，以及 PR #5 2D LiDAR / ToF mandatory sensor material 仍缺。
- Objective 2 / Objective 3：不推进 completion。本轮不证明真实 dropoff/cancel completion、Nav2/fixed-route、route/elevator field pass、route completion signal、task record 或 delivery success。

## 3. KR 拆解

KR-A：Callback intake contract

- 输入：上一轮 `mobile_real_device_field_trial_acceptance_execution_pack*` summary / execution pack reference / same safe `evidence_ref`。
- 输入：现场 owner 后续提交的 callback packet。
- 输出：accepted / missing / rejected callback evidence。
- 输出：same safe `evidence_ref` check、owner handoff、`next_required_evidence` 和 rerun guidance。
- 边界：`software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_intake_gate`。

KR-B：Mobile/web 只读展示

- 展示 callback intake status、accepted evidence、missing evidence、rejected evidence、same-evidence-ref status、owner handoff、next required evidence、rerun guidance。
- 保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。
- 保持 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

KR-C：Robot diagnostics safe alias

- 暴露 `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary` 或等价 phone-safe summary。
- 只读消费 callback intake summary，不发送 ACK、cursor、Start、Confirm Dropoff、Cancel 或任何 robot command。
- 缺 summary、schema mismatch、unsafe evidence_ref、missing material 或 rejected callback 均 fail closed。

KR-D：Product closeout

- 后续 closeout 必须更新 sprint `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- 不得提高 OKR 百分比，除非真实手机材料、真实 external cloud 材料或真实硬件/HIL 材料到位并被对应验收命令证明。

## 4. 本轮核心抓手

从“现场 owner 已拿到 execution pack”推进到“现场 owner 有回调材料入口”。这比继续写本地 O5/O1/O2-O3 wrapper 更有价值，因为它为真实 iPhone/Android / production app / PWA prompt/user choice 材料回填建立了清晰路径，同时不越界宣称真实验收完成。

## 5. 需要做什么

- Full-stack owner 在 mobile/web 和 fixture 中新增 callback intake 只读 panel 与测试。
- Robot owner 在 operator gateway diagnostics 中新增 safe alias 与 targeted unittest。
- Product owner 后续根据 engineer 结果完成 closeout、OKR 和 progress log。
- 所有 owner 必须同步对应 docs：Full-stack 更新 `docs/product/mobile_user_flow.md`；Robot 更新 `docs/interfaces/ros_contracts.md` 或现有 diagnostics docs；Product 更新 closeout 和 progress log。

## 6. 优先级和验收口径

P0：证据边界正确

- 必须出现 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_intake_gate`。
- 必须保持 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须明确不证明真实手机、真实 route/elevator、HIL、O5 external 或 PR #5 hardware materials。

P0：Callback evidence 分类正确

- accepted callback evidence 只能表示字段齐备、same safe `evidence_ref` 对齐、材料可供下一步 review。
- missing callback evidence 必须给出 `next_required_evidence`。
- rejected callback evidence 必须给出 rejected reason 和 rerun guidance。
- unsafe evidence_ref、schema mismatch、raw artifact、credentials、ROS topic、serial/UART、`/cmd_vel`、完整 checksum 或 control copy 必须 fail closed。

P1：用户触点可理解

- 手机端应中文优先展示状态、缺口、负责人和下一步。
- 不暴露 raw JSON、ROS topic、串口、云密钥、DB/queue URL、OSS AK/SK、local path、traceback、complete artifact 或 checksum。

P1：工程围栏

- 只跑 targeted mobile/diagnostics/product 文件存在、`rg`、`py_compile`、`node --check`、targeted unittest 和 scoped `git diff --check`。
- 不跑 Docker/Humble、不跑 broad test suite。

## 7. 对应责任 Engineer

- User Touchpoint Full-Stack Engineer：`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/web/test_mobile_web_entrypoint.py`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/web/fixtures/status.json`、`docs/product/mobile_user_flow.md`。
- Robot Platform Engineer：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/ros_contracts.md` 或现有 diagnostics docs。
- Product Manager / OKR Owner：sprint closeout docs、`OKR.md`、`docs/process/okr_progress_log.md`。

## 8. 风险、阻塞和证据链

- 真实手机证据仍缺：需要 iPhone/Android device behavior、production app 或真实 PWA prompt/user choice 材料。
- Objective 5 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- Objective 1 / PR #5 仍缺：WAVE ROVER/UART/HIL、真实 bottom feedback、2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；`PRRT_kwDOSWB9286CJ3tX` 不能关闭。
- Objective 2 / Objective 3 仍缺：真实 task record、dropoff/cancel completion、Nav2/fixed-route runtime log、route completion signal、route/elevator field pass、delivery result。

## 9. 不证明事项

本轮不证明真实 iPhone、真实 Android、production app、真实 PWA prompt/user choice、真实 phone/browser acceptance、真实 cloud external proof、真实 4G/SIM、真实 OSS/CDN live traffic、真实 production DB/queue、真实 worker/cutover、真实 WAVE ROVER、真实 UART、HIL、真实 2D LiDAR / ToF material、真实 route/elevator field pass、真实 Nav2/fixed-route、dropoff completion、cancel completion、delivery success 或 `safe_to_control=true`。
