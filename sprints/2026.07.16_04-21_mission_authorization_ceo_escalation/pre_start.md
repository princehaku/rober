# Pre Start - Mission authorization CEO escalation

## Sprint metadata

- `sprint_type: epic`
- Sprint 状态：`authorization_refreshed_phase_a_frozen_pending_confirmed_subagent_runtime_recovery`
- Product owner：`product-okr-owner`
- Engineering owners（仅授权后按顺序）：`robot-algorithm-engineer` → `rober-hardware-engineer` → `full-stack-software-engineer`
- Proof boundary：`fresh_authorization_present_no_business_runtime_recovery_no_live_result`

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

## 2026-07-20 后续 automation turn 准入覆盖

CEO 再次 fresh 明确小车运动授权、operator 看护、路线清空和物理位置受限，因此安全 `authorization=true`，上述 frozen identity 保留。但 fresh authorization 只刷新现场安全门禁，不构成 `subagent_runtime` 业务执行通道恢复证据。上一 automation turn 的三个 Algorithm dispatch 均在业务文件或命令前 stall，且 `tech-done.md` / `final.md` 已明确禁止无恢复信号的第四次 continuation。

本轮 Product 裁决为 `ROUTE=NONE`；Algorithm Phase A 从旧的 ready 口径覆盖为 `frozen_pending_confirmed_subagent_runtime_recovery`，Hardware 与 Full-stack 继续等待，不派任何 Engineer。只有 runtime owner 给出与当前 worker 池关联的修复确认，或另一个真实业务 Engineer 在 repo 内完成业务文件写入并运行至少一条业务验收命令的可核验证据，才可复用本 sprint 和 frozen identity 重开；Product/read-only worker 成功、`/tmp` canary、仅 `pwd`/`git status`、新 automation turn 或再次授权均不算恢复信号。

## 2026-07-20 fresh authorization blocker reset 后的最终准入事实

CEO 本轮明确要求“持续推进 OKR”，并再次确认小车运动授权、物理位置受限、operator 看护、路线清空。依据 `AGENTS.md`“CEO 明确继续攻坚同一 blocker 后计数重置”例外，本轮对既有 runtime blocker 执行且只执行一次 `blocker reset`；这一 reset 只允许重新尝试业务执行，不等于 runtime 已恢复，也不产生 OKR credit。

主节点先后派发 `algorithm_bounded_route` 与窄上下文 fallback `algorithm_route_fallback`。两者经明确催促后仍停滞在业务文件或业务命令之前，并被中止；均未 SSH，未执行 ROS/Nav2、stop、goal、`T=1001`、测试或构建。planned helper/test/doc/artifact 仍不存在，live helper 调用次数=`0`、goal 调用次数=`0`、pre-stop=`0`、post-stop=`0`。因此本轮 `authorization 未消费`。

本节覆盖上一节的“本轮不派 Engineer”调度判断，但不改写其历史事实。最新门禁为 `safety_gate=true_for_this_turn`、`execution_gate=false`；精确 blocker 为 `subagent_runtime_stalled_before_business_file_or_command_execution_after_fresh_authorization`，不是 repo、SSH、ROS、Nav2 或硬件失败。Mission Objective 0 保持 `paused`；O5/O6/O7/O1 保持 `85% / 93% / 93% / 94%` flat，`okr_credit=false`，KR `不归档`。禁止继续派相同 worker 或新开 wrapper；下一步只能由当前 worker pool runtime owner 提供修复版本、恢复时间和业务成功证据，或由 CEO 指定其他 Objective。
