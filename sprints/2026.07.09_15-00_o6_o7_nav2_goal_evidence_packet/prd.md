# O6/O7 Nav2 Goal Evidence Packet PRD

## 用户价值和产品北极星

O6/O7 现在已经能消费同一 `task_id` 下的 route、replay、keyframe 与 field motion packet，但用户真正关心的下一步是“机器人是否有一条可解释的 Nav2 目标执行记录”。如果 Nav2 goal/result 仍只存在于独立 proof JSON 或脚本输出里，O6 无法把它纳入任务归档，O7 也无法在历史回放和标注界面解释为什么当前还不能宣称送达成功。

本轮产品北极星仍是“普通手机用户可验证地把垃圾交给机器人完成投递”。本 sprint 的产品结果只定义 Nav2 goal evidence packet 计划，让后续工程把 O11 proof JSON 变成可归档、可回读、可展示的 evidence 摘要。

## OKR 映射和方向判断

- 目标 Objective：O6、O7。
- 当前最低 active Objective：O6 与 O7，并列约 50%。
- 方向判断：继续推进 O6/O7。
- 方向依据：O3 现场 lane 仍是更高优先级，但本轮通过消费 O11 Nav2 goal execution proof，把现场路线/运动证据进一步接入 O6/O7，可同时推进 O6 的归档 readback 与 O7 的历史回放/标注消费。
- 不调整 O1/O2/O3/O4/O5：本轮不做真实硬件控制、真实手机验收、真实生产云、真实电梯或真实送达闭环。

## 问题定义

已有事实：

1. `field_motion_evidence_packet` 已能归一同一 `task_id` 的 `map.yaml/.pgm`、`route.csv`、keyframes、remote_capture motion logs 与 `derived_replay.jsonl`。
2. `onboard/scripts/o11_nav2_goal_execution_proof.py` 已存在，可产出 Nav2 goal execution proof JSON。
3. 最新 final 已明确下一步要补 `nav2_goal_result_or_delivery_record`，并继续保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

当前缺口：

1. O11 proof JSON 尚未作为 `nav2_goal_execution_evidence` 接入 `field_motion_evidence_packet`。
2. O6 archive detail / consumer detail 尚未白名单回读同一 `task_id` 的 Nav2 goal/result 摘要。
3. O7 consumer detail 尚未用同一摘要展示 readiness、blocked reasons、next evidence。
4. 当前仍缺真实 production cloud、真实 route bag、真实 live Nav2 run、真实 delivery record 与真实送达成功证据。

## 本轮核心抓手

定义一条并行实现 sprint：

- Algorithm 把 O11 proof JSON 提炼为 `nav2_goal_execution_evidence`，并接入 field motion packet。
- O6 把该摘要纳入 archive/readback 白名单，继续阻断危险字段和危险 true。
- O7 把该摘要展示为只读 readiness，不打开主动作、不宣称真实送达。
- Product 在后续实现完成后收口 OKR、sprint 文档与证据边界。

## 需求范围

### In scope

- 定义 additive `nav2_goal_execution_evidence` 摘要名称和字段边界。
- 输入来源限定为 O11 proof JSON 或 fixture，围绕同一 `task_id` 与 `field_motion_evidence_packet` 关联。
- O6 archive detail / consumer detail 白名单回读该摘要。
- O7 consumer detail 展示 readiness、blocked reasons、next required evidence 与 proof scope。
- 继续 fail-closed 处理危险 true、path、root、token、raw、base64 与 unsafe refs。

### Out of scope

- 真实 production cloud / production DB / queue / OSS / CDN / TLS / 4G。
- 真实硬件控制、真实 `/cmd_vel` 执行、真实底盘动作或真实 WAVE ROVER feedback。
- 真实 live Nav2 run 已完成、真实 delivery record 已完成或真实送达成功。
- 新建与 O11 proof、field motion packet 无关的 local/mock wrapper。

## 验收口径

本轮 planning docs 验收必须满足：

1. 三份文档均标注 `sprint_type: epic`。
2. 明确 O6/O7 是最低 active Objective，且 O3 现场 lane 更高优先级。
3. 明确本 sprint 通过 O11 proof 消费现场路线/运动证据来推进 O6/O7。
4. 明确 Algorithm/O6 Robot Software/O7 Full-stack 三个 owner 并行，Product 后续收口。
5. 明确 `nav2_goal_execution_evidence` 是 additive 摘要，且命名在文档中保持一致。
6. 明确危险 true/path/root/token/raw/base64 fail-closed。
7. 明确 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

后续实现验收必须满足：

1. Algorithm 能从 O11 proof JSON 产出同一 `task_id` 的 `nav2_goal_execution_evidence`。
2. O6 能 ingest/readback 该摘要，且只暴露安全白名单字段。
3. O7 能展示该摘要对应的 readiness、blocked reasons、next evidence。
4. 所有测试、build、lint、`git diff --check` 按 `tech-plan.md` 通过。

## 风险、阻塞和需要补齐的证据链

- O11 proof JSON 可能与现有 packet 的 `task_id`、proof scope 或字段命名存在差异，后续实现需要先做 additive 映射。
- 如果 proof 只证明离线或 fixture 级别 Nav2 goal execution，O6/O7 必须保留 `software_proof` 边界。
- 若 O7 展示文案过强，容易被误解为真实送达或真实控制完成，必须用 blocked reasons 与 next evidence 明确剩余缺口。
- 真实 `route_bag`、真实 live Nav2 pose progress、真实 delivery record 仍需要后续 sprint 补证。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

本轮只是计划留档，不归档任何 KR。后续实现若通过，也只能作为 O6 KR2/KR6 与 O7 KR3/KR4 的增量证据，除非真实 production cloud、真实数据回灌、真实 route replay/labeling 与真实送达证据齐备，否则不得把 KR 标为完成。

## 需要创建或更新的 sprint 文档

本轮只创建或更新：

- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/pre_start.md`
- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/prd.md`
- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/tech-plan.md`

后续实现完成后再创建或更新 `tech-done.md`、`side2side_check.md`、`final.md`，并由 Product 决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
