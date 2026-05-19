# Sprint 2026.05.19_21-22 Real Material Evidence Intake - Pre Start

## 1. Sprint 类型

- sprint_type: epic
- Sprint 目标：新增 `real_material_evidence_intake` 统一真实材料回填入口，让 field owner 能按 material group 提交、归档和复核真实材料 manifest。
- 证据边界：当前主机只有 Docker，没有真实硬件、真实手机、真实公网、真实 4G/SIM、真实 OSS/CDN live traffic 或 production DB/queue。所有本轮实现和验证只能作为 `software_proof`，默认 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 2. 开工依据

CEO 本轮要求：开始下一轮迭代，根据近期 PR 和评审建议下一步深入的 OKR；用 team 继续完成 OKR；重新在功能往前走；测试只做围栏；优先推进 OKR 完成度低；本机没有真实硬件，只有 Docker；最后提交并推送。

本轮不更新 `OKR.md`，只创建下一轮 Epic sprint 的前三份计划文档：`pre_start.md`、`prd.md`、`tech-plan.md`。

## 3. 用户价值和产品北极星

用户价值：把“缺真实材料”从散落在 O5、O1/PR #5、PR #4 route/elevator、O4 real phone 的阻塞说明，推进成一个可回填、可归档、可复核、可被 Robot diagnostics 和 mobile/web 只读消费的统一入口。

产品北极星：每个真实世界能力声明都必须能追溯到同一 safe `evidence_ref` 下的真实材料 manifest；缺失、驳回和待补材料必须显式 fail closed，不能被 mobile/web 或 Robot diagnostics 误读成真实通过、HIL、route/elevator field pass、real phone proof、external proof 或 delivery success。

## 4. OKR 映射

- Objective 5：当前约 68%，是 live `OKR.md` 4.1 数字最低项；但继续提高需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover 或真实 external proof。Docker-only 主机不能生成这些材料。
- Objective 1：当前约 81%，是次低项；PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry，也缺 WAVE ROVER/UART/HIL。
- Objective 2 / Objective 3：PR #4 route/elevator 已多轮 wrapper，仍缺真实 route/elevator field materials、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel material 和 delivery result。
- Objective 4：real-phone 链已多轮 wrapper，仍缺真实 iPhone/Android device behavior、production app、PWA prompt/user choice 和 true phone/browser acceptance。

## 5. 上轮未完成项和重复 blocker 核对

- 最新 sprint `sprints/2026.05.19_20-21_real-material-readiness-board/final.md` 已交付统一 readiness board，只能展示四类真实材料缺口和 next_required_evidence，不能证明真实材料已提交或通过。
- 不能再做单纯缺口展示；本轮必须新增材料回填 intake，把现场 owner 的真实材料 manifest 纳入可验证 artifact。
- PR #4 / route/elevator 与 O4 real-phone 链已多轮 wrapper，不能重复消费同一真实材料 blocker。
- O5 外部 proof 和 O1/PR #5 硬件 proof 仍缺真实材料；本轮只能搭建 intake contract 和 fail-closed software proof，不提升 OKR 百分比。

## 6. 本轮核心抓手

本轮主抓 `real_material_evidence_intake`：

- 统一接收 O5 external、O1/PR #5 hardware、PR #4 route/elevator、O4 real phone 四类 material group 的 manifest。
- PC gate 生成 fail-closed intake artifact，明确 `accepted_items`、`missing_items`、`rejected_items`、`same_evidence_ref`、`next_action` 和 `not_proven`。
- Robot diagnostics 只读消费 sanitized summary，不暴露原始材料、路径、凭证、checksum 或控制语义。
- mobile/web 只读显示 intake status、accepted/missing/rejected items、safe `evidence_ref` 和 next action，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

## 7. 需要做什么

- 创建 PC gate：`pc-tools/evidence/real_material_evidence_intake.py`，按 material group 校验真实材料 manifest 并生成 artifact。
- 增加 PC 单测：覆盖 accepted/missing/rejected、unsafe evidence_ref、跨 group 缺失、O5/O1/PR #5/PR #4/O4 fail-closed 边界。
- 更新 Robot diagnostics：增加 `robot_diagnostics_real_material_evidence_intake_summary` phone-safe summary。
- 更新 mobile/web：新增只读 “真实材料回填入口” panel，仅渲染白名单字段。
- 更新 docs：接口文档、ROS contract、mobile user flow 同步说明 evidence boundary。
- 生成 sprint evidence artifact：用于本轮 Docker-only software proof。

## 8. 责任 Engineer

- Hardware/Autonomy owner：主责 PC gate、测试、接口文档和 sprint evidence artifact。该 owner 覆盖真实材料 manifest 的 product contract，但不得声明真实硬件或现场材料已到位。
- Robot owner：主责 Robot diagnostics summary、diagnostics unittest、ROS contract 文档。该 owner 只消费 sanitized summary，不读取原始材料。
- Full-Stack owner：主责 mobile/web 只读 panel、fixture、mobile entrypoint test 和 product docs。该 owner 不改变 primary action gating。

## 9. 风险、阻塞和证据链

- 最大风险：实现时把 intake artifact 写成真实材料通过。防线：所有 artifact 和 UI 默认保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- O5 风险：没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover proof，本轮不得提高 Objective 5。
- O1 / PR #5 风险：`PRRT_kwDOSWB9286CJ3tX` 缺真实 2D LiDAR / ToF 与 WAVE ROVER/UART/HIL 材料，本轮不得关闭 thread 或提高 Objective 1。
- PR #4 / O4 风险：route/elevator 和 real-phone 已多轮 wrapper，本轮只有统一 intake 入口，不声明 field pass 或 true phone proof。

## 10. 需要创建或更新的 sprint 文档

本轮开工前创建：

- `sprints/2026.05.19_21-22_real-material-evidence-intake/pre_start.md`
- `sprints/2026.05.19_21-22_real-material-evidence-intake/prd.md`
- `sprints/2026.05.19_21-22_real-material-evidence-intake/tech-plan.md`

实现完成后必须继续补齐：

- `sprints/2026.05.19_21-22_real-material-evidence-intake/tech-done.md`
- `sprints/2026.05.19_21-22_real-material-evidence-intake/side2side_check.md`
- `sprints/2026.05.19_21-22_real-material-evidence-intake/final.md`
