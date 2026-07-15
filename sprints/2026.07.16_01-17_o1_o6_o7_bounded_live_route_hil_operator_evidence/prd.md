# PRD - 有界路线执行与同窗口 HIL/operator 证据

## 产品目标

把现有 planner-only、28-pose packet、route gate、mock execution、readback 与 historical feedback 材料推进到一次真实、可审计、可安全停止的 current-run mission attempt。北极星是让 O6/O7 收到同一 task/run/route lineage 的真实 route/HIL/operator evidence，而不是继续扩大 support-only surface。

## OKR 映射与方向判断

- O5 约 `85%`：`暂停`。真实 provider/runtime blocker 已连续消费两轮，本 sprint 不再探测或包装。
- O6/O7 各约 `93%`：`继续`。主要缺口包含真实 live Nav2 route execution、delivery/operator material 和真实机器人数据。
- O1 约 `94%`：`联动继续`。主要缺口包含 current live WAVE ROVER same-run HIL、nonzero wheel feedback、stop 后归零和 safe execution evidence。
- KR：本轮计划阶段不归档；没有完成 KR 可移入历史区。

## 用户故事

作为现场 operator，我希望在明确授权且站在机器人旁边时，只允许一次短距离 Nav2 goal，并能在同一证据包里看到：执行前 stop 可用、goal 请求与终态、执行中/执行后 `T=1001` wheel feedback、执行后归零、现场观察和 cleanup。这样即使失败，也能知道真实任务卡在哪里，而不是再看一层 readiness 文案。

## Phase 0 授权需求

本 PRD 不把“持续推进 OKR”或 `ssh root@192.168.1.11 -p 37878` 解释为运动授权。进入 engineering 前必须获得 fresh explicit authorization：exactly one `NavigateToPose`，目标固定 `map (0.8, 0.25, yaw=0)`，operator 在场、路线清空、stop ready、同意 pre/post stop 与 `T=1001` capture，并明确 no retry/no `/initialpose`/no manual/no unattended motion。

未授权时的产品状态固定为 `blocked_pending_explicit_live_motion_authorization`。不得用 mock、fixture、历史 artifact、readback 或计划文档代替授权和 live attempt。

## 功能需求

### FR1 - 单一命令与 lineage

- 只允许一个 goal attempt，绑定 `mission_task_id`、`run_id`、`route_intent_id`、`authorization_ref`。
- goal 坐标固定，禁止扩大为完整 28-pose route 或第二个目标。
- 记录 accepted/rejected/timeout/canceled/succeeded/aborted 原始终态与时间边界。

### FR2 - HIL 与 stop 证据

- live 前确认 stop endpoint 与 operator stop 路径 ready；执行 pre-stop。
- 同窗口采集 vendor base feedback `T=1001`，只接受包含 `L/R/r/p/y/v` 的合法帧。
- live 后无条件 post-stop，并记录 post-stop `L/R=0/0` 或明确 fail-closed blocker。
- 硬件事实采用 `docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h` 与 vendor feedback tutorial；本 sprint 不改串口、波特率、速度映射、固件或硬件配置。

### FR3 - Operator evidence

- 记录 operator 是否在场、是否确认路线清空、是否观察到运动、是否接受安全收尾。
- operator 文本不能替代 goal result、stop record 或 `T=1001` material。

### FR4 - O6/O7 条件消费

- 只有 live artifacts clean 后才允许同一 task 写入 O6 archive，并由 O7 consumer 显示 mission attempt、route terminal result、feedback 与 operator evidence。
- 不新增只读 wrapper endpoint；复用现有 archive/task detail/consumer detail 主路径。
- raw UART、绝对路径、credential、host、token、任意 URL 和危险 true claim 必须 fail closed 或脱敏。

## 验收口径

### 未授权验收

- 三份计划文档明确授权 hard gate；没有 engineering 文件、live command、SSH/ROS/UART invocation 或 artifacts。
- `authorization_gate=false`、所有 mission/control delta 为 false、OKR 百分比保持不变。

### 获授权后的最小验收

- exactly one goal invocation；pre/post stop 都有记录；同窗口至少有合法 `T=1001` material；operator report 有明确时间与同源 lineage；cleanup 没有残留受管进程。
- 失败终态仍可算 `mission_attempt`，但不得写 `route_execution_success=true`、`hil_pass=true`、`safe_to_control=true` 或 `delivery_success=true`。
- 只有 route success、硬件反馈、post-stop、operator acceptance 同时 clean，Product 才能考虑更高 credit tier；delivery 仍需独立交付事实。

## 非目标与 anti-repeat

- 不重跑 O5 provider/tunnel、`/scan`、camera、localization bag wrapper 或 business canary。
- 不新增 preflight/readback/export/browser/mock receipt/status panel。
- 不把 planner-only path、28-pose packet、mock execution、historical wheel feedback 或 fixture 当 current-run route/HIL evidence。
- 不进行 `/initialpose`、manual control、直接 `/cmd_vel`、第二次 goal、无人值守运动或完整路线扩张。

## Proof boundary

当前边界为 `planning_only_blocked_pending_explicit_live_motion_authorization`。它不证明 SSH 可用、ROS graph ready、Nav2 ready、WAVE ROVER safe、route execution、delivery、HIL、operator acceptance 或 Mission Objective 0；也不产生 OKR credit。
