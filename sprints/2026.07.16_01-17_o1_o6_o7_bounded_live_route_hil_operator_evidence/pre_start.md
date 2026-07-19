# Pre-start - O1/O6/O7 有界 live route、HIL 与 operator evidence

## Sprint metadata

- `sprint_type: epic`
- 状态：`planning_blocked_pending_explicit_live_motion_authorization`
- 主受益 Objective：O6/O7（各约 `93%`）
- 联动 Objective：O1（约 `94%`）
- Proof boundary：`planning_only_blocked_pending_explicit_live_motion_authorization`
- Sprint 路径：`sprints/2026.07.16_01-17_o1_o6_o7_bounded_live_route_hil_operator_evidence/`

## 上轮事实与 blocker 去重

1. O5 约 `85%` 仍最低，但 public tunnel/provider runtime 同一外部 blocker 已在最近两轮消费；本轮按红线暂停 O5。
2. `2026.07.15_20-07_o6_o7_live_localization_bag_replay` 已多次停在 business sub-agent 编排层，最终明确禁止再次派同一 Algorithm wrapper、再次做 canary，或转去 `/scan`、camera、preflight/readback/export/browser/mock wrapper。
3. 最近审计已确认：未消费的 strict-no-motion lane 已耗尽。下一种能越过 support-only 上限的材料必须包含 current-run motion attempt、同窗口硬件反馈或 operator action，而不是另一层合同包装。

## 用户价值与产品北极星

用户需要的不是“已准备执行”的 packet，而是一次有边界、可停止、可审计的真实路线尝试：同一 `mission_task_id/run_id/route_intent_id` 下，记录 Nav2 `NavigateToPose` 终态、运动前后 stop、WAVE ROVER `T=1001` 反馈和现场 operator 观察，形成可供 O6/O7 消费的 current-run mission-attempt evidence。

## 本轮核心抓手与范围

计划中的唯一 live 动作是：在 CEO/operator 明确授权后，向 `map` 坐标系 `(0.8, 0.25, yaw=0)` 发出一次 bounded `NavigateToPose`，并在同窗口完成 pre-stop、post-stop、`T=1001` 采集和 operator evidence。默认禁止 retry、第二个 goal、`/initialpose`、manual control、直接 `/cmd_vel`、无人值守运动或扩大路线。

本轮当前消息只提供了 SSH 地址。SSH 连接信息不等于运动授权，也不等于 operator 在场、路线清空、stop 可用或 HIL 准入。因此本轮停在 Phase 0；不得执行 SSH live 命令、Nav2 goal、stop、UART、ROS 写操作或任何运动。

## Owner 与组织方式

- 主责：`robot-algorithm-engineer`。授权后统一编排唯一 goal、路线终态和 mission lineage，避免多个 owner 各自发送控制命令。
- 支持：`rober-hardware-engineer`。授权后按 vendor 资料验证 pre/post stop 与同窗口 `T=1001` 反馈，不得发送独立运动命令。
- 条件消费：`full-stack-software-engineer`。只有 Algorithm/Hardware frozen artifacts clean 后才允许进入 O6/O7 同 task 消费；不得使用 fixture 冒充 live。
- Product：`product-okr-owner` 只做授权 gate、验收与 OKR/closeout 判断。

## 开工 gate

工程派单必须同时看到一条 fresh explicit authorization，至少写明：

1. 授权 exactly one bounded `NavigateToPose` 到 `map (0.8, 0.25, yaw=0)`；
2. operator 已在现场、路线已清空，并能立即触发 stop；
3. 同意 pre/post `/api/base/stop` 与同窗口 `T=1001` 反馈采集；
4. 接受 no retry、no `/initialpose`、no manual control、no unattended motion；
5. 授权有效时间窗和执行 owner。

缺任一项即 `authorization_gate=false`，本 sprint 不进入 engineering，不获得 OKR credit。

## 预期验收与风险

- 最低可接受结果是一次有 lineage 的 current-run mission attempt，即使 Nav2 失败或 abort，也必须有 stop、反馈和 operator 事实，不能伪造 `route_execution_success=true`。
- 只有真实终态、同窗口 nonzero/zero feedback、operator acceptance 与安全收尾同时满足，Product 才评估 O1/O6/O7 是否上调。
- 任意 pre-gate、stop、feedback、localization、controller 或 operator 条件失败都 fail closed；不重试、不换入口。
- 当前剩余 blocker 是 CEO/operator 的显式 live-motion 授权，不是 SSH、ROS、Nav2 或 WAVE ROVER 故障，因为这些路径本轮没有触达。

## 2026-07-20 fresh authorization hardware-first continuation

`ROUTE=HARDWARE_PRE_GATE`，`authorization=true`。CEO 已 fresh authorization：小车运动已授权，物理位置受限，operator 看护且路线清空。冻结 identity 为 `AUTHORIZATION_REF=ceo_20260720_rober_okr_bounded_motion_v1`、`RUN_ID=run_20260720_rober_okr_bounded_route_01`、`task_id=task_o1_bounded_live_route_20260720_01`、`route_intent_id=route_o1_map_0p8_0p25_20260720_01`。

本 continuation 将 Phase 1 `Hardware pre-gate` 设为 ready：先派 `rober-hardware-engineer` 只执行 current live pre-stop、合法 WAVE ROVER `T=1001` 反馈采集和 operator physical gate，不发送独立运动命令。该路径属于 O1 尚未消费的 current-live stop/feedback 证据，不是再次包装或重派已反复 stall 的 Algorithm worker。任一 Hardware gate 不 clean 即 stop、no retry；只有 Hardware clean 后才允许派 `robot-algorithm-engineer` 执行 frozen identity 下 exactly one bounded goal，仍保持 no retry。当前不提前写 `tech-done.md`、`side2side_check.md` 或 `final.md`，KR 不归档，OKR 百分比不变。
