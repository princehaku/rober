# Sprint 2026.05.20_06-07 Cloud Command Idempotency Visibility Guard - Side2Side Check

## 1. 验收对象

- 用户价值：重复云指令不会让机器人重复执行本地 action，手机端能看懂“重复云指令已去重，不是送达成功”。
- 产品北极星：云中转控制面在弱网、重试、重复提交时保持 fail-closed、可诊断、可复盘。
- 证据边界：`software_proof_docker_cloud_command_idempotency_visibility_guard`

## 2. PRD 对照

| PRD 要求 | 验收结果 |
| --- | --- |
| Duplicate command cached ACK 不重复提交本地 action | 通过。Robot worker 报告 duplicate 不重复提交 backend action，focused tests 覆盖。 |
| Robot/operator status 输出 duplicate/deduped 状态 | 通过。状态包含 `command_duplicate_deduped`、`duplicate_command_id`、`cached_ack_state`、`ack_semantics=duplicate_cached_ack_not_delivery_success`、`remote_ready=false`、`primary_actions_enabled=false`。 |
| expired duplicate 与 pending terminal ACK 优先级不被遮盖 | 通过。Robot worker 修复 stale/pending priority 与 `ack_semantics` 检查后重跑通过。 |
| mobile/web 展示中文安全文案并禁用主操作 | 通过。Full-Stack worker 报告 cloud readiness panel 消费 `command_duplicate_deduped`，Start/Confirm/Cancel disabled。 |
| 不新增 auto replay / auto resubmit / endpoint | 通过。Full-Stack worker 报告无自动重放、无自动 resubmit、无新增控制 endpoint。 |
| docs/product 和 sprint closeout 保守同步 | 通过。`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md` 已由 Engineer 更新；Product closeout 同步 OKR/progress/sprint docs。 |

## 3. OKR 最低优先级回顾

- 当前最低 Objective 仍是 Objective 5，约 68%。
- 本 sprint 针对 Objective 5 的 command/status/ack 幂等可见性，属于具体功能安全缺口，不是重复包装外部 proof blocker。
- Objective 5 不提高 completion，因为没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser。
- Objective 1 不提高 completion，因为 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false`，真实 2D LiDAR / ToF 和 HIL materials 仍缺。

## 4. 验收结论

本轮通过 Product side-by-side check，可进入 final closeout。可接受的产品结论是：

- `cloud_command_idempotency_visibility_guard` 已形成 Docker/local software proof。
- Duplicate command cached ACK 可见、fail-closed、不会被写成 delivery success。
- 手机用户看到的语义是“重复云指令已去重；机器人没有重复执行；这不是送达成功”。

不可接受的外推结论：

- 不得写成真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/cutover 已通过。
- 不得写成真实手机/browser、Nav2/fixed-route、WAVE ROVER/UART/HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success。
- 不得写成 PR #5 `PRRT_kwDOSWB9286CJ3tX` 已 resolved。
