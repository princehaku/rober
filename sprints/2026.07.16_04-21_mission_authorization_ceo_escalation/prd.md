# PRD - Mission authorization CEO escalation

## 背景与问题

当前最低 Objective 是 O5（约 `85%`），但 provider/runtime 根因已连续两轮未解，第三轮继续消费违反 blocker 红线。O6/O7 各约 `93%`，O1 约 `94%`；它们共同缺少的 mission-grade 证据是当前窗口的真实有界路线、同窗底盘反馈与 operator 现场确认。

现有 SSH endpoint `root@192.168.1.11:37878` 只是连接信息。上一轮已正确拒绝把它解释为真实运动授权；因此本轮产品问题不是“再做一层软件证明”，而是请 CEO 对唯一有风险的现场动作给出明确授权或暂停决定。

## 用户价值

授权 clean 后，团队只执行一次受约束的真实任务尝试，直接验证机器人是否能在 operator 看护下从停止状态完成一个短目标并再次安全停止；结果无论成功或失败都保留真实终态，不用 mock/support artifact 替代。

未授权时保持零工程动作，避免因含糊指令触发物理运动，也避免用更多 wrapper 虚增进度。

## 决策用户故事

作为 CEO/operator，我需要看到动作、地点、安全前提、执行次数、停止手段和禁止项的完整授权文本，以便明确决定是否允许本次真实运动，并知道没有明确授权时系统不会连接或执行。

作为 Product owner，我需要把授权与 mission evidence lineage 绑定，只有同一 authorization/run/task/route 窗口的真实材料才可进入验收，且失败事实不能被布尔成功字段覆盖。

## Fresh authorization contract

只有 CEO/operator fresh 消息完整确认以下内容，`authorization=true` 才成立：

> 授权在 operator 现场看护、路线已清空且 stop ready 的前提下，执行 exactly one bounded `NavigateToPose` 到 `map (0.8, 0.25, yaw=0)`；允许 pre/post stop 与同一窗口 WAVE ROVER `T=1001` 反馈采集；禁止 retry、`/initialpose`、manual control、直接 `/cmd_vel` 和无人值守运动。

还必须记录 authorization 时间窗和执行 owner。缺任一条件均为 `authorization=false`，全部工程 phase 保持 disabled。

## 功能需求

### FR-1 授权门禁

- 仅 fresh CEO/operator 明示授权可打开门禁。
- SSH endpoint、历史授权、笼统“继续”、测试要求或连接成功均不能打开门禁。
- 授权前禁止 SSH、ROS、测试、构建、部署、capture 与任何物理动作。

### FR-2 唯一有界动作

- 唯一目标：`map (0.8, 0.25, yaw=0)`。
- `goal_invocation_count` 最大且只能为 `1`；任何 timeout、abort、reject、cancel、采集失败或 partial artifact 都不得 retry。
- 必须有 pre-stop、bounded terminal wait、unconditional post-stop 与 cleanup。
- 禁止 `/initialpose`、manual、直接 `/cmd_vel`、UART 直控与 unattended motion。

### FR-3 同窗口 HIL 与 operator 证据

- operator 必须现场看护，且在发送 goal 前确认 route clear、stop ready。
- 记录合法 `T=1001` 的运动/停止窗口事实，保留原始终态和 stop 后反馈。
- operator observation 只作为现场验收材料，不能替代 route terminal result、stop response 或底盘反馈。

### FR-4 顺序消费

- owner 严格按 `robot-algorithm-engineer` → `rober-hardware-engineer` → `full-stack-software-engineer` 顺序执行。
- Full-stack 只能消费冻结且结构断言 clean 的真实 Algorithm/Hardware artifacts；不得使用 fixture/mock 进入 mission success 路径。
- 不新增 endpoint，不再生产 packet、gate、readback、browser、export 或 mock-only wrapper。

### FR-5 诚实验收

- Route 的 succeeded/aborted/rejected/timeout/cancel/blocked 原样记录。
- `route_execution_success` 只能由真实成功终态决定。
- route 成功不自动等于 `delivery_success=true`；只有现场 delivery 事实才能判定 delivery。
- `hil_pass` 必须依赖同窗口合法反馈与 post-stop 事实；`safe_to_control` 不得由单次成功自动推导。
- OKR credit 与 KR 归档只由 Product 在实际证据完成后决定。

## 验收口径

### 本规划 sprint 验收

- Epic 三份前置文档按顺序存在，且授权文本、owner、严格文件范围、工程验收命令和风险边界完整。
- 清楚记录 O5 blocker 两轮红线与本轮 CEO escalation。
- 清楚记录授权前全部 Engineering disabled，且没有执行 SSH/ROS/测试/构建。
- Closeout 文档只能记录 planning/CEO escalation 的实际变更、验证范围与 blocker，不得冒充工程完成证据；不修改 `OKR.md`，百分比与 KR 状态保持不变。

### 授权后工程验收

- 同一 authorization/run/task/route lineage 完整。
- exactly one goal，目标精确匹配，pre/post stop 完整，cleanup residual 为 `0`。
- 同窗合法 `T=1001` 与 post-stop zero/停止事实可核验。
- operator presence、route clear、stop ready 与观察结果均有记录。
- Full-stack 仅在上游 clean 后消费真实 artifacts；任一 fail-closed 条件触发时停止后续 phase。

## 非功能与安全要求

- Safety-first、fail closed、no retry、no unattended motion。
- Engineer 必须遵守 `AGENTS.md` 的 owner 边界、中文技术注释 `>20%` 与硬件 vendor 资料复核要求。
- 一个 live session 只有一个控制编排者，禁止多个 owner 并发发 goal 或 stop。
- 日志不得把 SSH 可达、ROS 可见、goal accepted 或 operator 口述误写为 mission success。

## 当前非成果边界

本 PRD 及其 blocked closeout 是 decision/planning artifact，不是 current-run mission artifact。状态为 `blocked_pending_fresh_ceo_motion_authorization_no_okr_credit`，proof boundary 为 `planning_and_ceo_escalation_only_no_engineering_or_live_execution`。当前固定：

- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `okr_credit=false`

O5/O6/O7/O1 百分比保持 flat，KR `不归档`。
