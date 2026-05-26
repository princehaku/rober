# Cloud Command Terminal Result Mainline Side2Side Check

## 1. 对照目标

本轮 Product closeout 对照 `pre_start.md`、`prd.md` 和 `tech-plan.md` 核对：是否从 `terminal_result_pending` 推进到 `terminal_result_recorded` 主链路，并且是否保持 fail-closed 产品口径。

## 2. 用户价值对照

| 目标 | 对照结果 |
| --- | --- |
| 手机用户能看到命令终态结果，不再只停留在 pending | 已满足。mobile/web 在命令结果核对面板展示 `terminal_result_recorded`、result type/code、error code、safe command/evidence 和下一步证据要求。 |
| 支持人员能按同一 `robot_id + command_id` 对账 | 已满足 software proof 口径。Robot API/store/query 都绑定同一 command，file-backed 和 SQLite-backed store 均持久化 terminal result。 |
| 终态结果不被误写成真实送达成功 | 已满足。worker 事实显示 UI 主操作不因 recorded 自动启用，所有状态继续 fail-closed。 |

## 3. PRD P0/P1 对照

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| robot-facing terminal result 写入入口 | 通过 | `POST /robots/{robot_id}/commands/{command_id}/terminal-result` |
| terminal result 持久化 | 通过 | file-backed 和 SQLite-backed store 持久化 terminal result |
| result reconciliation 返回 recorded | 通过 | `trashbot.cloud_command_result_reconciliation.v2` 返回 `terminal_result_recorded` |
| ACK-only 仍 pending | 通过 | focused unittest 覆盖 ACK-only 仍 `terminal_result_pending` |
| conflict/missing/store_unavailable fail-closed | 通过 | focused unittest 覆盖 conflict、missing、store_unavailable |
| mobile/web 展示 recorded 与中文 fail-closed copy | 通过 | “命令结果核对”面板覆盖 recorded、pending、conflict、missing、store_unavailable |
| 主操作不因 recorded 自动启用 | 通过 | Full-Stack worker 验证覆盖 |

## 4. OKR 最低优先级回顾

`tech-plan.md` 标注最低 Objective 是 Objective 5，约 76%。本 sprint 直接命中 Objective 5，并从 result reconciliation pending 推进到 terminal result mainline。Product closeout 判断本轮可保守提升 Objective 5 到约 80%，但不提升 Objective 1/2/3/4。

## 5. 反验收核对

- 未发现本轮只是 review/handoff/material/intake wrapper。
- 未发现只改 mobile fixture 而不改 backend。
- 未发现 terminal result 只存在响应、不落 store 的证据。
- 未发现 query API 仍只能返回 `terminal_result_pending`。
- 未发现把 `completed`、`dropoff_completed` 或 `cancel_completed` 写成真实 delivery success 的 closeout 证据。

## 6. 证据边界

本轮证据边界是 `software_proof_docker_cloud_command_terminal_result_gate`。它证明 repo 内 API/store/query/UI 的 local software proof 主链路，不证明公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、true phone/browser proof、HIL、Nav2/fixed-route、WAVE ROVER/UART 或真实 delivery success。
