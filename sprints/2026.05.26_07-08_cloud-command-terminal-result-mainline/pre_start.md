# Cloud Command Terminal Result Mainline Pre-Start

## 1. Sprint 声明

- sprint_type: epic
- sprint_id: `2026.05.26_07-08_cloud-command-terminal-result-mainline`
- automation: `daily-bug-scan`
- 启动时间：2026-05-26 07:08 Asia/Shanghai
- 当前仓库：`/mnt/e/rober`
- 当前 HEAD：`550f6b1 Add PC hardware material coverage`
- 工作树边界：仅允许本 sprint 三个规划文档；`.idea/rober.iml` 是范围外改动，禁止触碰。

## 2. 上轮输入

上一轮 Objective 5 已完成 `cloud_command_result_reconciliation`：

- phone/cloud 已能查询 queued、processing、terminal_result_pending、missing_or_expired、store_unavailable。
- terminal ACK 仍只是 command lifecycle envelope，不是真正 task terminal result。
- mobile/web 能解释这些状态，但仍不能展示同一 `command_id` / `robot_id` 下由 robot/relay 写入并持久化的 terminal result。

本轮不能继续做 metadata-only wrapper、support handoff、review decision、材料回填面板或只读解释层。必须规划成真实 API/store/UI 主路径。

## 3. 用户价值和产品北极星

产品北极星仍是：普通手机用户把垃圾交给小车后，通过云端中转看到任务从发起、处理到终态的可信闭环，而不是只看到一个 queued receipt 或 terminal ACK。

本轮用户价值：

- 用户可以用手机看到“这条命令最终由机器人上报了什么结果”，不再停在 `terminal_result_pending`。
- 支持人员可以按同一 `robot_id + command_id` 对账：命令、ACK、terminal result、证据边界是否一致。
- 系统继续 fail-closed：即使有软件侧 terminal result，也不能在缺少真实 field/HIL/送达材料时宣称 `delivery_success=true`。

## 4. OKR 映射

- 直接目标：Objective 5 云中转 + OSS/CDN 数据通路产品化。
- 当前快照：Objective 5 约 76%，为全局最低；Objective 1 约 83%，Objective 2/3/4 约 99%。
- 本轮目标推进：把 O5 从“terminal_result_pending 可解释”推进到“cloud command terminal result mainline 可写入、可持久化、可查询、可展示”。
- 非目标：不提升 Objective 1/2/3/4；不证明 WAVE ROVER/UART/HIL、Nav2/fixed-route、真实电梯、真实送达、真实手机设备、生产公网、真实 4G/SIM 或 OSS/CDN live traffic。

## 5. KR 拆解

- KR5.1：Robot/cloud relay 提供 robot-facing terminal result 写入入口，绑定同一 `robot_id` 与 `command_id`。
- KR5.2：command store 持久化 terminal result，支持 file-backed 和 SQLite-backed proof store 的最小读写路径。
- KR5.3：result reconciliation API 返回新的 terminal result 状态，而不是继续只有 `terminal_result_pending`。
- KR5.4：mobile/web 展示 terminal result 终态、结果类型、错误码、证据边界和下一步证据要求。
- KR5.5：所有路径保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`，直到真实 field/HIL/送达材料补齐。

## 6. 本轮核心抓手

核心抓手是“主链路写入和查询”，不是“再加一个解释面板”：

1. Robot/relay 接收 terminal result。
2. Store 按 `robot_id + command_id` 持久化 terminal result。
3. `GET /api/commands/{command_id}/result?robot_id=<robot_id>` 返回 terminal result recorded 状态。
4. mobile/web 在现有 command result reconciliation 面板显示该终态。
5. sprint closeout 再更新 `OKR.md`、`docs/product/` 和剩余风险。

## 7. Owner 和责任边界

- Product Manager / OKR Owner：本轮只负责 `pre_start.md`、`prd.md`、`tech-plan.md`，定义用户价值、验收口径、范围边界和 owner。
- Robot Software Engineer：负责 cloud relay API、store、result reconciliation contract、backend tests 和相关 cloud docs。
- User Touchpoint Full-Stack Engineer：负责 mobile/web 展示、fixture、UI tests 和 mobile flow docs。
- Hardware Infra Engineer：本轮不实施；真实 field/HIL/送达材料仍是后续硬件/现场 owner。
- Robot Algorithm Engineer：本轮不实施；Nav2/fixed-route runtime 和 route/elevator field pass 不在本轮范围。

## 8. 风险、阻塞和证据链缺口

- 主要风险：实现如果只新增 `terminal_result_material_*` 或 safe summary wrapper，会继续卡在 metadata-only，不能提升 O5。
- 数据一致性风险：terminal result 必须绑定已有 command，不允许创建孤儿结果或跨 robot_id 写入。
- 安全风险：terminal result 可能包含 raw artifact、traceback、路径、token 或硬件字段；必须脱敏。
- 产品风险：`completed` 或 `dropoff_completed` 文案容易被误读成真实送达成功；UI 和 API 必须同时写清 software proof 边界。
- 证据缺口：本轮不提供公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser、WAVE ROVER/HIL、Nav2/fixed-route runtime 或 delivery success。

## 9. 本轮需要创建或更新的 sprint 文档

本轮启动阶段创建：

- `sprints/2026.05.26_07-08_cloud-command-terminal-result-mainline/pre_start.md`
- `sprints/2026.05.26_07-08_cloud-command-terminal-result-mainline/prd.md`
- `sprints/2026.05.26_07-08_cloud-command-terminal-result-mainline/tech-plan.md`

实现和收口阶段必须继续创建或更新：

- `sprints/2026.05.26_07-08_cloud-command-terminal-result-mainline/tech-done.md`
- `sprints/2026.05.26_07-08_cloud-command-terminal-result-mainline/side2side_check.md`
- `sprints/2026.05.26_07-08_cloud-command-terminal-result-mainline/final.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/mobile_user_flow.md`
- `OKR.md`
