# Sprint 2026.05.19_21-22 Real Material Evidence Intake - PRD

## 1. 用户价值和产品北极星

用户价值：现场 owner 拿到真实材料后，可以按统一 material group 回填 manifest；产品、Robot diagnostics 和 mobile/web 都能看到同一 safe `evidence_ref` 下哪些材料被接受、缺失或驳回，以及下一步该补什么。

产品北极星：真实能力必须由真实材料驱动，软件只负责 intake、归档、复核和 fail-closed 展示。没有真实材料时，系统必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`，不能把 readiness、ACK、summary、browser proof 或 local Docker proof 写成真实通过。

## 2. 背景和问题

live `OKR.md` 4.1 显示 Objective 5 约 68%，是当前最低 Objective；但它需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或 external proof。Docker-only 主机无法生成这些材料。

Objective 1 约 81%，是次低 Objective；PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry，也缺 WAVE ROVER/UART/HIL。

上一轮 `real_material_readiness_board` 已统一展示 O5 external、O1/PR #5 hardware、PR #4 route/elevator、O4 real phone 四类缺口。下一步不能继续展示缺口，而要提供真实材料回填 intake，让 field owner 交付材料时有统一入口和明确复核结果。

## 3. OKR 映射

- Objective 5：本轮提供 O5 external material group 的回填入口和 fail-closed artifact，但没有真实公网、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover proof，因此不提高完成度。
- Objective 1：本轮提供 PR #5 hardware material group 的回填入口和 PR thread 状态引用；没有真实 2D LiDAR / ToF、WAVE ROVER/UART/HIL 材料，不关闭 `PRRT_kwDOSWB9286CJ3tX`。
- Objective 2 / Objective 3：本轮提供 PR #4 route/elevator material group 的回填入口，要求同一 safe `evidence_ref` 下的真实 route/task/elevator/dropoff/cancel/delivery materials；没有材料时保持 not_proven。
- Objective 4：本轮提供 real phone material group 的回填入口，只读展示真实手机/PWA/production app 材料状态；没有真实设备材料时保持 not_proven。

## 4. KR 拆解或更新

KR-1：PC evidence gate 能读取 material manifest，按 material group 输出 intake artifact。

- O5 external required items：HTTPS/TLS public ingress proof、4G/SIM proof、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover evidence 或等价 external proof。
- O1 / PR #5 hardware required items：2D LiDAR / ToF SKU、source、receipt、procurement、installation、wiring、power、calibration、HIL-entry；WAVE ROVER/UART/HIL packet 仍需真实材料。
- PR #4 route/elevator required items：Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material、delivery_result。
- O4 real phone required items：real iPhone/Android behavior、production app、PWA prompt/user choice、true phone/browser acceptance。

KR-2：Robot diagnostics 消费 PC summary，输出 phone-safe diagnostics summary。

- 只允许展示 summary schema、intake status、material group、safe evidence_ref、accepted/missing/rejected counts 和 next action。
- 不允许读取或展示原始材料、凭证、完整路径、checksum、raw JSON、ROS topic、UART/serial low-level details 或控制授权。

KR-3：mobile/web 增加只读真实材料回填入口 panel。

- 显示 intake status、accepted/missing/rejected items、same safe `evidence_ref`、next action 和 evidence boundary。
- Start Delivery、Confirm Dropoff、Cancel 保持 fail closed，不因材料回填 panel 改变 gating。

KR-4：文档和 sprint evidence 同步。

- 更新接口文档、ROS contract、mobile user flow。
- 生成 sprint evidence artifact，明确是 Docker-only `software_proof`，不是真实材料通过。

## 5. 本轮核心抓手

`real_material_evidence_intake` 是 readiness board 后的下一层真实材料入口：

1. Field owner 按 material group 准备 manifest。
2. PC gate 验证 manifest 结构、安全 evidence_ref 和 required items。
3. Gate 输出 accepted/missing/rejected 结果和 next action。
4. Robot diagnostics 和 mobile/web 只读展示 sanitized summary。
5. 若真实材料缺失，结果必须 fail closed 并保持 `not_proven`。

## 6. 需要做什么

- Hardware/Autonomy：实现 `pc-tools/evidence/real_material_evidence_intake.py`、测试、接口文档和 sprint evidence artifact。
- Robot：实现 diagnostics summary 映射、unittest、`docs/interfaces/operator_gateway_diagnostics.md` 和 `docs/interfaces/ros_contracts.md` 同步。
- Full-Stack：实现 mobile/web 只读 panel、fixture/test 和 `docs/product/mobile_user_flow.md` 同步。

## 7. 优先级和验收口径

P0：PC gate fail-closed artifact。

- 验收：material manifest 缺失或不安全时必须输出 missing/rejected，不得输出 pass、delivery success、safe_to_control 或 primary action enabled。

P0：Robot diagnostics phone-safe summary。

- 验收：diagnostics 只消费 sanitized summary，字段白名单明确，缺 summary 时 fail closed。

P0：mobile/web 只读 panel。

- 验收：panel 能显示 intake status、accepted/missing/rejected items 和 next action；primary action gating 不变。

P1：文档同步和 sprint evidence。

- 验收：`docs/interfaces/real_material_evidence_intake.md`、`docs/interfaces/operator_gateway_diagnostics.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 记录新 contract 和 evidence boundary。

## 8. 对应责任 Engineer

- Hardware/Autonomy owner：真实材料 manifest contract、PC gate、artifact 和 docs/interfaces/real_material_evidence_intake.md。
- Robot owner：operator_gateway_diagnostics summary、diagnostics unittest、operator diagnostics 文档和 ROS contract。
- Full-Stack owner：mobile/web panel、fixture/test 和 mobile user flow 文档。

## 9. 非目标

- 不更新 `OKR.md`。
- 不关闭 PR #5 `PRRT_kwDOSWB9286CJ3tX`。
- 不声明 Objective 5 external proof、Objective 1 HIL、PR #4 route/elevator field pass 或 Objective 4 real phone proof。
- 不读取或提交真实凭证、OSS AK/SK、DB/queue URL、完整原始材料、硬件序列号敏感信息或本地绝对路径。
- 不改变 Start Delivery、Confirm Dropoff、Cancel 控制授权。

## 10. 风险、阻塞和证据链

- 真实材料仍可能为空：这是预期场景，artifact 应输出 missing items 和 next action。
- material group 可能跨 Objective：必须使用 material group 和 evidence_ref 明确归档，不用单一 Objective 名称覆盖事实。
- 工程实现可能误把 accepted manifest item 写成真实通过：验收必须要求 `not_proven` 和 fail-closed copy。
- 当前证据链只到 Docker-only `software_proof`；真实 OKR 提升要等现场材料回填、复核并在 final/OKR 中保守更新。

## 11. 需要创建或更新的 sprint 文档

已创建或本轮计划创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
