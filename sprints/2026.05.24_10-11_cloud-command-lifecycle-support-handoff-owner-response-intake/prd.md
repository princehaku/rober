# Cloud Command Lifecycle Support Handoff Owner Response Intake PRD

Run time: 2026-05-24 10:11 Asia/Shanghai

## 产品目标

交付 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake`：一个只读、fail-closed 的 owner/support response intake，用于承接上一轮 support handoff bundle 的安全上下文，并接收未来真实外部 O5 材料或明确缺失/拒绝/unsafe 状态。

该能力必须证明“系统可以安全接收并分类 owner/support response metadata”，不能证明真实云、真实手机、verified terminal result、HIL 或 delivery success。

## 用户价值和产品北极星

普通用户不应该看到一串无法判断真假的 ACK、pending safe id 或 support copy。支持同学和 field owner 也不能靠人工聊天猜测下一步材料是否到了、是否安全、是否可复核。

本轮的用户价值是把支持交接后的材料入口标准化：当真实外部材料还没到时，系统明确标记 missing；当 owner 拒绝或材料 unsafe 时，系统明确拒绝并保留 blocked 原因；当材料可接受时，系统只进入 review-ready，不把它升级为 delivery success。

产品北极星：云端中转不是单次 demo，而是用户可理解、支持可复盘、工程可追责的远程送达控制链。

## OKR 映射

### Objective 5：云中转 + OSS/CDN 数据通路产品化

本轮直接服务 Objective 5，但不提升百分比。Objective 5 仍约 68%，no OKR percentage lift。

映射 KR：

- KR1：继续围绕 `trashbot.remote.v1` command/status/ack 的安全状态解释，保持 accepted/processing only 与 terminal result pending 的边界。
- KR5：继续强化凭证和敏感字段不入仓、不暴露，owner/support response intake 必须拒绝 raw secret、local path、ROS topic、serial/UART、WAVE ROVER、traceback、complete artifact 或 success copy。
- KR6：继续强化 graceful degradation；外部材料缺失、拒绝或 unsafe 时必须可恢复、可解释，而不是默认成功。

### Objective 4：手机用户体验

本轮可能新增 mobile/support read-only panel，但只证明 Docker/local UI 可以展示 intake 状态。它是 not true phone/browser proof。

### Objective 1/2/3

本轮不改变硬件协议、route/elevator、Nav2/fixed-route 或任务终态；不解决 PR #5 `PRRT_kwDOSWB9286CJ3tX` / `hardware_material_pending`。

## KR 拆解或更新

本轮不更新 `OKR.md` KR 文案，不提升 OKR 百分比。执行层 KR 拆解如下：

1. Intake source KR：从上一轮 support handoff bundle 的 safe copy、pending-safe command/evidence、`owner_handoff`、`next_required_evidence` 读取来源，并拒绝缺少 source boundary 或同一 safe `evidence_ref` 的材料。
2. Classification KR：输出 accepted、missing、rejected、unsafe、blocked 分类，每类都必须包含 owner/support 可理解原因和 next required evidence。
3. Fail-closed KR：强制保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
4. Surface KR：mobile/support 面板只读展示 intake 结果和 safe copy，不新增 replay/resubmit、ACK/cursor、review mutation、material upload、GitHub mutation 或 robot control path。
5. Evidence KR：所有验证只落在 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate`，并在 docs 和 sprint closeout 中明确 no OKR percentage lift。

## 本轮核心抓手

把“support handoff 已准备好给 owner”推进到“owner/support response 可以被安全接入和分类”，但不把 response intake 伪装成外部材料已到、PR 已解决或终态结果已验证。

## 需要做什么

- Full-Stack：在 `mobile/web` 增加只读 owner response intake panel、fixture 和针对性单测；同步 `docs/product/mobile_user_flow.md`。
- Robot/API：先只读确认上一轮 HTTP export/support bundle 是否已有足够 safe fields；如缺少 compatibility alias，再在 Robot/API diagnostics/status 中补只读 safe alias，不新增控制路径；同步 `docs/product/remote_4g_mvp.md`。
- Product：实现完成后更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`，并只在 closeout 阶段更新 `OKR.md` 4.1 与 `docs/process/okr_progress_log.md`，保持 Objective 5 no OKR percentage lift。

## 优先级和验收口径

P0:

- Intake 必须只消费 safe support handoff source，不接受 unsafe/raw 字段。
- 必须输出 accepted/missing/rejected/unsafe/blocked。
- 必须保留 false-state flags：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 必须写明 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate`。

P1:

- mobile/support panel 只读展示并支持 safe copy，不新增控制端点。
- Robot/API safe alias 仅在确实缺 compatibility 时新增。
- docs/product 同步说明 proof boundary 和禁止声明。

P2:

- Product closeout 把下一步真实材料缺口清晰写入 sprint final 和 OKR snapshot。

验收成功定义：

- 目标字符串 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake` 出现在实现、fixture、docs 和 sprint closeout。
- 证据边界 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate` 出现在实现、fixture、docs 和 sprint closeout。
- 测试证明 unsafe/raw materials fail closed，missing/rejected 状态不会启用 Start/Confirm/Cancel，不会触发 replay/resubmit 或 ACK/cursor mutation。
- closeout 明确 no OKR percentage lift、not true phone/browser proof、not public HTTPS/TLS、not 4G/SIM、not OSS/CDN live traffic、not production DB/queue、not worker/cutover、not verified terminal result、not HIL、not PR #5 resolved、not delivery success。

## 对应责任 Engineer

- User Touchpoint Full-Stack Engineer：mobile panel、fixture、mobile tests、`docs/product/mobile_user_flow.md`。
- Robot Platform Engineer：Robot/API diagnostics safe alias 或 compatibility read-only consultation、Robot tests、`docs/product/remote_4g_mvp.md`。
- Product Manager / OKR Owner：sprint closeout、OKR 边界、验收口径、风险复盘。

Hardware Infra Engineer 本轮不改硬件，因为 PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，且本机没有真实硬件、真实手机、真实公网云或 4G/SIM。Autonomy Algorithm Engineer 本轮不参与实现，因为不改 Nav2、route/elevator 或 task terminal runtime。

## 风险、阻塞和证据链

阻塞：

- public HTTPS/TLS 缺失。
- 4G/SIM 缺失。
- OSS/CDN live traffic 缺失。
- production DB/queue 缺失。
- worker/cutover 缺失。
- true phone/browser 缺失。
- verified terminal result 缺失。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。

风险：

- 继续叠加 Docker/local metadata 容易被误读为 Objective 5 真实进展，因此 closeout 必须写 no OKR percentage lift。
- owner response intake 可能被误读成真实材料已到，因此状态文案必须区分 accepted for review 与 delivery success。
- mobile/support panel 若暴露 raw material、ACK/cursor 或 control routes，会破坏 fail-closed 边界。

证据链要求：

- 只允许 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate`。
- 不允许写成 external cloud proof、true phone/browser proof、HIL、verified terminal result 或 delivery success。

## 需要创建或更新的 sprint 文档

本 planning run 创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现和验收必须补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
