# Cloud Command Result Reconciliation Pre Start

## 1. Sprint 声明

- sprint_type: epic
- sprint_id: `2026.05.26_08-09_cloud-command-result-reconciliation`
- 目标能力：`cloud-command-result-reconciliation`
- 启动时间：2026-05-26 08:00 Asia/Shanghai
- 责任链路：Product Manager / OKR Owner 规划与验收；Robot Software Engineer 与 User Touchpoint Full-Stack Engineer 并行执行。

## 2. 用户价值和产品北极星

北极星仍是普通手机用户不用 SSH、ROS2、串口或 raw JSON，也能通过手机发起垃圾投递任务、看到可信状态、知道下一步该等还是该找支持。

上一轮已经让手机端能通过同源 cloud command API 把任务级命令入队，但用户现在只能拿到 queued receipt。queued 只能证明云端接收了命令，不能证明机器人已领取、正在执行、取消完成、投放完成或送达成功。本轮要补齐用户最需要的下一段状态解释：刚入队的 command 能被手机端用 phone-safe 查询到 ack / result / pending 状态，并且所有 copy 和接口都必须明确 queued、processing、terminal 都不等于 delivery success。

## 3. OKR 映射

- Objective 5：云中转 + OSS/CDN 数据通路产品化，当前约 72%，仍是最低 Objective。
- 直接命中的 KR：KR1 commands/status/ack 最小契约、KR6 4G/云链路 graceful degradation 语义。
- 间接受益：Objective 4 手机用户体验，用户能看到更可信的任务状态，但本轮不把本地软件证明当 true phone/browser proof。

## 4. 上轮输入和未完成项

上一轮 `sprints/2026.05.26_00-01_cloud-phone-command-api-mainline` 已完成：

- `POST /api/commands/collect`
- `POST /api/commands/confirm-dropoff`
- `POST /api/commands/cancel`
- `mobile/web` 主动作切到 `/api/commands/*`
- receipt 强制保留 `ack_semantics=queued_not_delivery_success`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`

上轮剩余风险明确指向：

- 命令入队不等于机器人执行完成。
- 仍缺 command result reconciliation。
- 仍缺 production DB/queue、多实例一致性、真实公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、真实手机/browser、HIL 和真实送达证明。

## 5. 本轮核心抓手

本轮不再新增另一个只读 metadata wrapper，也不把队列入队继续包装成进度。核心抓手是把上一轮 command enqueue 后的查询与对账补上：

- 手机端/同源 API 能按 `robot_id + command_id` 查询 command lifecycle summary。
- 状态至少区分 `queued`、`processing`、`terminal`、`missing_or_expired`、`store_unavailable`。
- Robot/API 侧只输出 phone-safe summary，不泄露 token、Authorization、raw state path、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、DB/queue URL 或完整 artifact。
- 文案和 contract 明确：queued / processing / terminal 只是云命令生命周期状态，不是 delivery success；terminal 也必须继续区分 ack terminal 与 verified delivery/dropoff/cancel result。

## 6. Owner 和并行策略

这是跨 2 个 owner 的 Epic sprint，文件范围互不重叠，必须并行派发：

- Robot Software Engineer：负责 relay/API/store 查询与 backend phone-safe summary contract。
- User Touchpoint Full-Stack Engineer：负责 mobile/web 同源查询、展示、fixture 和手机产品文档。

Product Owner 本轮只负责计划、验收口径和后续 closeout，不改产品代码、不跑实现测试。

## 7. Blocker 重复消费检查

最近两轮没有把同一根因 blocker 作为 final 主要结论连续消费两次。上一轮是功能前进到 phone -> cloud command enqueue，本轮继续沿 Objective 5 最低项推进到 result reconciliation，不属于重复卡在 Docker registry、真实串口、OSS 凭证或外部材料缺失。

## 8. 本轮启动风险

- 本轮仍是 software proof 级别，不能承诺真实公网、4G、production DB/queue 或真实送达。
- 如果只做 UI 面板而没有 backend 查询 contract，不允许 closeout 为 OKR 进度提升。
- 如果 backend 查询返回 terminal ack，却没有 verified delivery/dropoff/cancel result，手机端必须继续显示不是送达成功。
- 实现完成后必须同步更新 `docs/product/remote_4g_mvp.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/mobile_user_flow.md` 或同等相关文档。
