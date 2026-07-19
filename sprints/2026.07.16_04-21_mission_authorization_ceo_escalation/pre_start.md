# Pre Start - Mission authorization CEO escalation

## Sprint metadata

- `sprint_type: epic`
- Sprint 状态：`reactivated_phase_a_ready_current_automation_turn_no_live_result_yet`
- Product owner：`product-okr-owner`
- Engineering owners（仅授权后按顺序）：`robot-algorithm-engineer` → `rober-hardware-engineer` → `full-stack-software-engineer`
- Proof boundary：`fresh_authorization_phase_a_ready_no_live_result_yet`

## 升级原因

O5 约 `85%`，是 `OKR.md` 4.1 当前最低 Objective；但同一 provider/runtime blocker 已连续消费两轮。按“同一 Blocker 重复消费红线”，本轮禁止第三次探测、包装或改写该 blocker，也不得转去另一个 wrapper/readback/mock-only surface。

上一轮 `2026.07.16_01-17_o1_o6_o7_bounded_live_route_hil_operator_evidence` 已把未消费的 mission 主线收敛为一次有界 live route + HIL + operator evidence，却因没有明确物理运动授权而 fail closed。继续创建离线 helper、mock gate，或重复打开同一 live work 再因无授权 blocked，不能产生用户价值；因此本轮升级 CEO 做唯一缺失的方向决策，并按 Epic 契约诚实收口规划事实。

本轮只建立决策与授权后的执行边界，不执行工程，不算 OKR 进展，不修改百分比，不归档 KR。

## 当前输入与授权边界

- 已知连接信息：`ssh root@192.168.1.11 -p 37878`。
- 该 endpoint 只说明可能的连接位置，不构成连接授权，更不构成 `NavigateToPose`、manual control、直接 `/cmd_vel`、UART、stop 或任何物理动作授权。
- 当前 `authorization=false`；operator 在场、路线清空、stop ready 均未获确认。
- 授权前全部 Engineering phase=`disabled_pending_fresh_ceo_authorization`；禁止 SSH、ROS、测试、构建、部署、采集与硬件操作。

## 请求 CEO 决策

CEO 需要明确选择其一：

1. 授权：operator 现场看护、路线已清空且 stop ready 时，执行 exactly one bounded `NavigateToPose` 到 `map (0.8, 0.25, yaw=0)`；允许 pre/post stop 与同一窗口 WAVE ROVER `T=1001` 采集；no retry、no `/initialpose`、no manual、no direct `/cmd_vel`、no unattended motion。
2. 不授权或暂停：保持全部工程 phase disabled，停止消费该 blocker，并由 CEO 指定其他 Objective/策略。

任何模糊同意、仅重复 SSH endpoint、仅要求“继续推进”或没有 operator/route/stop 条件的消息均按未授权处理。

## 本轮目标与非目标

### 目标

- 形成可逐字确认的 authorization contract。
- 固定授权后唯一执行链、owner 顺序、文件范围、验收命令和 fail-closed 条件。
- 防止第三轮消费 O5 blocker，以及防止授权缺失时再次生产 support-only artifact。

### 非目标

- 不连接 `192.168.1.11:37878`，不读取 live ROS graph。
- 不运行 `NavigateToPose`、`/initialpose`、manual、`/cmd_vel`、UART 或 stop。
- 不写工程代码、测试或配置；closeout 只记录规划、升级、验证范围与 blocker，不伪造工程完成证据。
- 不声明 `route_execution_success`、`delivery_success`、`hil_pass` 或 `safe_to_control`。

## 当前 Mission / OKR 状态

- O5：约 `85%`，flat；本轮不消费 provider/runtime blocker。
- O6/O7：各约 `93%`，flat。
- O1：约 `94%`，flat。
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `okr_credit=false`
- KR：`不归档`

## Sprint 文档门禁

本轮先顺序建立 `pre_start.md`、`prd.md`、`tech-plan.md`，authorization gate=false 后不启动任何 Engineer、不预生成工程完成证据；随后用 `tech-done.md`、`side2side_check.md`、`final.md` 只收口 planning/CEO escalation 的实际事实、验证范围与 blocker。

## 2026-07-20 fresh authorization reactivation（本轮冻结口径）

CEO fresh 原话：`小车运动已经授权，我已经限制了它物理位置，不会有风险。我已授权有 operator 看护、路线清空`。据此冻结 `authorization=true`，授权窗口仅限当前 2026-07-20 automation turn，operator owner=`CEO-designated on-site operator`，且以 operator 看护、路线清空、物理位置受限持续成立为前提；执行入口为 `ssh root@192.168.1.11 -p 37878`。O5 `85%` 的 blocker `2/2` 不重开，O6/O7 保持 `93%`；本轮只解锁 O1 `94%` 的 live route/HIL 缺口，不形成新的完成结论。

本轮唯一执行 identity 为 `AUTHORIZATION_REF=ceo_20260720_rober_okr_bounded_motion_v1`、`RUN_ID=run_20260720_rober_okr_bounded_route_01`、`task_id=task_o1_bounded_live_route_20260720_01`、`route_intent_id=route_o1_map_0p8_0p25_20260720_01`。目标固定为 `map (0.8, 0.25, yaw=0)`；Algorithm helper 当前不存在，故 `Phase A ready` 的顺序是先实现并通过离线测试，再由同一 helper live 执行 exactly one 次，no retry，且必须执行 pre-stop 与 post-stop。禁止 `/initialpose`、manual、direct `/cmd_vel`、direct UART、unattended；Hardware 只读冻结 artifact，Full-stack 仅在 clean 时消费。
