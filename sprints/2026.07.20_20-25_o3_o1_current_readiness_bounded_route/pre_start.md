# O3/O1 Current Readiness + Bounded Route - Pre Start

## Sprint metadata

- `sprint_type: epic`
- 状态：`planning_complete_pending_engineer_dispatch`
- Product owner：`product-okr-owner`
- 主责集成与唯一 live-control owner：`robot-software-engineer`
- 专业验收：`robot-algorithm-engineer`、`robot-hardware-engineer`、`full-stack-software-engineer`
- 目标 Objective：O3 current readiness supporting，条件通过后推进 O1/O6/O7 current route/HIL/user-action evidence
- proof boundary：由真实 `READINESS_GO`、route terminal、stop/T1001 和 receipt 结果决定；planning 本身 `okr_credit=false`

## 新鲜 gate change

CEO 本轮原文：

> 上位机在ssh root@192.168.1.11 -p 37878. 小车运动已经授权，我已经限制了它物理位置，不会有风险。我已授权有 operator 看护、路线清空；持续推进 OKR。

本消息建立新的 automation-turn 授权与现场上下文：operator 在场、路线清空、物理活动范围受限，并允许小车运动。它不自动证明 Nav2/current pose/TF/path、stop ready、障碍状态、WAVE ROVER feedback、route success、HIL、delivery 或 safe-to-control；这些必须由本轮 current artifact 逐级证明。

本轮沿用既有受限目标 `map (0.8, 0.25, yaw=0)`、exactly one execute、pre/post stop、same-window `T=1001`、no retry、no `/initialpose`、no manual、no direct `/cmd_vel`、no unattended motion。任何 unknown 都 fail closed。

## 上轮事实与 blocker 去重

- O5 约 `85%` 最低，但 provider/runtime blocker 已消费 `2/2`，本轮禁止第三次 tunnel/provider/wrapper/readback。
- O6/O7 各约 `93%`，O1 约 `94%`；可计分缺口仍是 current route execution、current user action、same-window hardware feedback/operator result。
- `2026.07.20_13-20` 已交付 strict-no-motion lifecycle/readiness 合同，但两个窗口均 NO-GO，且出现 helper 80s/partial race；禁止复用那两个窗口。
- `2026.07.20_17-23` 已离线修复 80s/final reserve，并明确下一入口只能是新授权下的一个 current proof；本轮正是 gate change 后的唯一新窗口。
- `2026.07.20_12-20` 已证明 direct-upper 只读 pre-gate 当时 lifecycle stopped；禁止再开 network/loopback wrapper。本轮直接启动受管 strict-no-motion runtime 并刷新 current proof。

## 本轮核心抓手

Phase A 先形成一次自然 final 的 current no-motion readiness artifact；只有严格 `READINESS_GO=true` 才进入 Phase B exactly-one bounded `NavigateToPose`。Phase B 后无条件执行 post-stop/readback；Hardware 只验证同窗 stop/T1001，Full-stack 只消费冻结 identity/receipt，不补跑控制。

## 硬停止条件

- Phase A start、proof、latest、artifact parse、freshness、path 或 cleanup 任一失败：`READINESS_GO=false`，route execute invocation=`0`。
- current obstacle clear 或 stop-ready 未被远端 status/feedback/stop preflight 证明：execute invocation=`0`。
- execute 一旦调用，不论 success/fail/timeout/unknown，永不重试；最多一次 post-stop，随后只读回收。
- 禁止 `/initialpose`、manual、direct `/cmd_vel`、UART 直控、第二个 goal、扩大路线、28-pose route、unattended motion。
- 任何 owner 不得把 HTTP 200、软件测试、operator 文本、T1001 frame identity或 path success 单独升级为 route/HIL/delivery/safe-to-control。

## 预期留档链

本 Epic 按 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md` 推进。Engineer 只在真实执行后写 `tech-done.md`；Product acceptance 才能更新 `side2side_check.md`、`final.md`、`OKR.md` 与 progress log。
