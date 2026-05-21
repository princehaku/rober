# Field Evidence Rerun Execution Result Acceptance Backfill PRD

Run time: 2026-05-21 12:02 CST

## 1. 用户价值和产品北极星

用户价值：现场 owner/support 已经拿到 execution-result acceptance packet，但其中仍有 missing/blocked 材料。用户需要一个受控回填入口，把真实现场材料整理为 sanitized backfill manifest，并明确哪些材料仍不可接受，避免把本地 Docker 证明、review reply 或 unsafe material 误写成真实送达成功。

产品北极星：`rober` 要成为普通手机用户可用的低成本自主垃圾投递机器人。用户最终关心的是一次送垃圾任务是否由真实路线、电梯、投放、手机和云/硬件证据支撑，而不是 repo 中又多一个 local wrapper。本轮只服务于真实材料进入下一步 review decision 的入口，不提升真实送达结论。

## 2. OKR 映射

- Objective 5：当前约 68%，最低完成度。由于没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser proof，本轮不提升 Objective 5。
- Objective 1：当前约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false`，comment `3269642220` 只是 software-proof reply，不是 reviewer resolution；本轮不提升 Objective 1。
- Objective 2/3/4：当前约 99%。本轮为真实 route/elevator/mobile field evidence 的回填入口服务，但不声明真实 route/elevator field pass、real phone/browser、dropoff/cancel completion 或 delivery_success。

## 3. KR 拆解或更新

本轮不修改 `OKR.md` 数字，只定义后续实现要满足的 KR-like acceptance slices：

1. Autonomy backfill gate 可以读取 acceptance packet 后的现场回填目录或 manifest，输出 `field_evidence_rerun_execution_result_acceptance_backfill` sanitized manifest。
2. Robot diagnostics 只消费 backfill safe summary，并保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。
3. Mobile/web 只显示“现场证据复跑执行结果验收回填”只读 panel，不启用 Start Delivery、Confirm Dropoff 或 Cancel。
4. Product closeout 只在实现完成后更新 sprint docs、`OKR.md` 和 `docs/process/okr_progress_log.md`，且保守记录 no OKR percentage lift unless real materials are provided.

## 4. 本轮核心抓手

`field_evidence_rerun_execution_result_acceptance_backfill` 是 acceptance packet 后的受控回填入口。

它必须做到：

- 只接受 sanitized field-owner backfill manifest，不把 raw field material 直接暴露到 Robot/mobile。
- 按同一 safe `evidence_ref` 组织 task record、Nav2/fixed-route runtime log、route completion signal、elevator evidence、dropoff/cancel completion、delivery result、true phone/browser evidence 等材料状态。
- 对 missing、blocked、unsafe、evidence-ref mismatch、success-claim、sensitive-material 等情况 fail closed。
- 保持 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate`、`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 需要做什么

Autonomy:

- 新增 PC evidence gate 和测试。
- 在 `pc-tools/README.md` 与 `docs/interfaces/evidence_contracts.md` 写清 backfill manifest contract、blocked reasons、safe summary 和证据边界。

Robot:

- 在 operator gateway diagnostics 中增加 backfill safe summary alias。
- 测试只覆盖 summary extraction、redaction/fail-closed 和既有 diagnostics 不回归。
- 在 `docs/interfaces/ros_runtime_contracts.md` 写清 Robot 只读消费边界。

Full-Stack:

- 在 mobile/web 增加 read-only backfill panel 和 fixture。
- 测试 panel 渲染、敏感字段不展示、三类主操作保持 disabled。
- 在 `docs/product/mobile_user_flow.md` 写清手机端只是回填可见性，不是真实手机/browser proof。

Product:

- 实现后更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 实现后只按证据更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，不得把本轮写成 Objective 5/O1/O2/O3/O4 percentage lift unless real materials appear.

## 6. 优先级和验收口径

P0:

- 所有输出必须保留 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate`。
- 所有面向 Robot/mobile 的状态必须保留 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 和 comment `3269642220` 必须被写作 unresolved/software-proof reply boundary。

P1:

- 同一 safe `evidence_ref` 的材料类别必须清楚：task record、Nav2/fixed-route runtime log、route completion signal、elevator evidence、dropoff/cancel completion、delivery result、true phone/browser evidence。
- unsafe/sensitive/raw material 必须被拒绝或只显示 sanitized safe summary。

P2:

- Docs copy 必须清楚说明不等于 real HIL、WAVE ROVER/UART、real field rerun、real phone/browser、O5 external proof 或 delivery_success。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：`pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill.py`、`pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_backfill.py`、`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`。
- Robot Platform Engineer：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/ros_runtime_contracts.md`。
- User Touchpoint Full-Stack Engineer：`mobile/web/app.js`、`mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill.json`、`mobile/web/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：current sprint docs、`OKR.md`、`docs/process/okr_progress_log.md` after implementation.

## 8. 风险、阻塞和需要补齐的证据链

- 真实 O5 external proof 缺失：public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover、production app/device proof。
- 真实 O1 materials 缺失：WAVE ROVER/UART/HIL、2D LiDAR / ToF source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved；comment `3269642220` 不得当成 reviewer resolution。
- 真实 route/elevator/mobile 材料缺失：真实 task record、Nav2/fixed-route runtime log、route completion signal、door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result、true phone/browser evidence。
- 本机只有 Docker，无真实硬件；本轮只能是 software-proof planning 和后续 software-proof implementation。

## 9. 需要创建或更新的 sprint 文档

Planning scope:

- `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/pre_start.md`
- `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/prd.md`
- `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/tech-plan.md`

Implementation closeout scope:

- `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/tech-done.md`
- `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/side2side_check.md`
- `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
