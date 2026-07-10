# O6/O7 Nav2 Goal Evidence Packet Final

## sprint_type: epic

Product 收口时间：2026-07-09 15:29 CST。

## 收口结论

本 sprint 完成。Algorithm → O6 → O7 已围绕同一 `task_id` 打通 `nav2_goal_execution_evidence` 的 software proof 主链路：Algorithm 从 O11 proof JSON 生成摘要，O6 能归档和回读，O7 能只读展示 readiness、blocked reasons、next required evidence 和 false safety fields。

本轮证据边界为 `software_proof_nav2_goal_execution_evidence_only`。它是 Nav2 goal/result 证据摘要进入数据链路的进展，不是 live Nav2、生产云或送达成功证明。

## 用户价值和产品北极星

用户价值是让“机器人是否有可解释的 Nav2 goal 执行证据”进入历史任务、回放和标注链路。产品北极星仍是普通手机用户可验证地完成垃圾投递；本轮只是补强证据链，不替代真实投递验收。

## OKR 映射和进度调整

- O6：约 50% → 约 53%。理由是 O6 archive/read model 已从 field motion packet 进一步接住 `trashbot.nav2_goal_execution_evidence.v1`，并通过 `Ran 156 tests in 53.382s OK` 验证。
- O7：约 50% → 约 53%。理由是 O7 consumer detail 和 UI 已能展示同一 `task_id` 的 Nav2 goal execution evidence 只读摘要，并通过 `npm run test` 3 files / `477 passed`、build、lint 验证。
- 方向判断：继续推进 O6/O7。O3 现场路线 lane 仍是更高优先级；O6/O7 下一步应消费真实或更接近现场的 Nav2/route/delivery 材料。
- KR 归档判断：不归档任何 KR。O6 KR2/KR6 与 O7 KR3/KR4 只增加软件证据，不达到真实生产云、真实数据回灌、真实路线回放或真实送达闭环完成标准。

## 核心证据

- Algorithm：新增 `--nav2-goal-proof-json`、`trashbot.nav2_goal_execution_evidence.v1`、`software_proof_nav2_goal_execution_evidence_only`，manifest 顶层和 field packet 都写入摘要；验证 `Ran 29 tests in 0.059s OK`。
- O6：新增 sanitizer/readback helper，支持 field evidence、artifact bundle、archive detail、consumer detail 与 include 回读；验证 `Ran 156 tests in 53.382s OK`。
- O7：UI 新增 Nav2 goal evidence 只读摘要，首次 TS2783 已修复；`npm run test` 3 files / `477 passed`，build/lint 通过。

## 安全旗标

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

## 未完成事项和风险

- 不证明真实 production cloud、真实 DB/queue、TLS/4G、OSS/CDN live traffic。
- 不证明真实 `route_bag`、真实 live Nav2 run、真实 NavigateToPose runtime、真实底盘运动或 wheel raw 非零。
- 不证明真实 delivery success、真实 annotation API/export、真实 dataset export、真实 PC/browser 现场验收。
- 若真实 O11 proof 携带路径、root、token、raw/base64 内容，会按本轮规则 fail-closed，需要采集侧提供安全裁剪版。

## 下一轮建议

优先安排一个能产出 `route_bag`、live Nav2 pose progress、真实或准现场 Nav2 result、媒体可访问证据或 delivery record 的 sprint。O6/O7 后续只应继续做能消费这些现场材料的链路，不再把单纯 review/handoff/readiness wrapper 当作主要成果。
