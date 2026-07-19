# Tech Done - Phase 0 授权 gate 收口

## Sprint metadata

- `sprint_type: epic`
- Engineering status：`blocked_before_engineering_pending_explicit_live_motion_authorization`
- Proof boundary：`planning_only_blocked_pending_explicit_live_motion_authorization`

## 实际改动

本轮只完成 Epic 前置计划：

- `pre_start.md`：记录 O5 blocker 切换、current mission-attempt 方向、owner 与授权 gate。
- `prd.md`：定义一次 bounded `NavigateToPose`、pre/post stop、同窗口 `T=1001` 与 operator evidence 的产品验收口径。
- `tech-plan.md`：定义 Phase 0 hard gate、后续 Algorithm/Hardware/Full-stack 文件范围、顺序与验收命令。

没有产品代码、测试代码、硬件配置、launch、业务文档、artifact、OKR 或进度日志改动。没有派 Engineering 执行，因为当前用户消息只给出 SSH 信息，没有提供一次真实运动所需的 fresh CEO/operator explicit authorization。

## 子 agent 执行事实

- 首个 `product-okr-owner` 规划 agent 建立 sprint 目录后，在业务文件与验收命令前持续无落盘，被中断。
- 无历史 Product fallback 读取派单后仍在业务文件与验收命令前无落盘，被中断。
- 前置计划由主节点按仓库允许的 bounded fallback 补齐；随后 Product closeout follow-up 再次停在 closeout 文件前，被中断。
- 没有派 `robot-algorithm-engineer`、`rober-hardware-engineer` 或 `full-stack-software-engineer`，因为 Phase 0 authorization gate 为 false。

本轮 agent blocker 为 `subagent_runtime_orchestration_timeout_before_business_file_or_command_execution`。它不是仓库代码、测试、SSH、ROS graph、Nav2、stop endpoint、UART、WAVE ROVER 或上位机故障，因为这些工程路径均未触达。

## 验证结果

前置计划完成后，主节点只运行文档级验收：

```text
rg required anchors: PASS
closeout absence gate before closeout: PASS
git diff --check -- <sprint>: PASS
combined exit code: 0
```

`rg` 命中了 `sprint_type: epic`、`OKR 最低优先级核对`、三类 owner、`explicit authorization`、`NavigateToPose`、`T=1001`、验收命令、Anti-repeat 和 Proof boundary。Engineering tests、build、SSH、ROS、Nav2、stop、UART、capture、HIL 与 live smoke 均未运行，也不得被声明为验证通过。

## OKR 与 mission 结果

- O5：约 `85%`，flat；同 provider/runtime blocker 已消费两轮，继续暂停。
- O6/O7：各约 `93%`，flat。
- O1：约 `94%`，flat。
- KR：`不归档`；无完成 KR 移入历史区。
- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`

由于没有 current-run/external/control/user-action delta，本轮不修改 `OKR.md` 或 `docs/process/okr_progress_log.md`，避免把计划或授权 blocker 写成进展。

## 剩余风险与下一步

唯一准入是 CEO/operator 明确授权 exactly one `NavigateToPose` to `map (0.8, 0.25, yaw=0)`，同时确认 operator 在场、路线清空、stop ready、允许 pre/post stop 和同窗口 `T=1001` capture，并接受 no retry/no `/initialpose`/no manual/no unattended motion。授权出现前，本 sprint 不允许实现离线 helper 来绕过 gate，也不允许再次消费 O5、`/scan`、camera、localization bag、canary 或 wrapper 类工作。

## 2026-07-20 hardware-first continuation closeout

Product 实际增量仅为在 `pre_start.md`、`prd.md`、`tech-plan.md` 追加 `ROUTE=HARDWARE_PRE_GATE` continuation，冻结 authorization/run/task/route identity，并把未消费的 O1 current-live Hardware pre-gate 排在 Algorithm 前。随后派出的真实 `rober-hardware-engineer` 经等待与催促仍停在任何允许业务文件、测试或 SSH/pre-stop 前，已被中止；hardware helper/test/doc/artifact 均不存在，`SSH=0`、`pre-stop=0`、`feedback capture=0`、`goal=0`，authorization 未消费。

精确失败为 `business_subagent_runtime_stalled_before_business_file_or_command_execution_across_product_and_hardware_owners`，不是 repo、SSH、ROS、Nav2 或 WAVE ROVER 失败。O5/O6/O7/O1=`85% / 93% / 93% / 94%` flat，`okr_credit=false`，KR `不归档`；不修改 `OKR.md` 或 progress log。禁止再次派 Algorithm/Hardware wrapper、fallback 或 canary。唯一 reopen signal：runtime owner 提供当前 worker-pool fix version、recovery time 与业务成功证据，或 CEO 指定其他 Objective。
