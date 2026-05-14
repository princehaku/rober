# Sprint 2026.05.15_05-06 Route Task Completion Signal - Side2Side Check

sprint_type: epic

## 1. 用户价值对照

PRD 用户价值要求：让普通手机用户和现场操作员知道一次 route/task 是否具备可解释的完成信号，并在材料缺失时知道下一步补什么。

本轮交付对照：

- Autonomy CLI 生成 completion artifact，汇总 fixed-route/task record、dropoff/cancel completion、failure/recovery 和 same `evidence_ref` 状态。
- Robot diagnostics 只读消费 completion summary，保持 metadata-only，不触发任何控制动作或 ACK。
- Mobile/web 只读展示 completion signal，普通用户可看到 `delivery_success=false`、`not_proven`、dropoff/cancel 缺口和下一步。

结论：满足 Docker/local completion signal 软件证据的产品闭环；不满足真实送达、真实投放、真实 cancel completed、真实 Nav2/fixed-route 或 HIL 验收。

## 2. PRD 验收对照

| PRD 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Autonomy 生成 `trashbot.route_task_completion_signal.v1` artifact | 通过 | CLI、8 条 targeted unittest、`--help`、required `rg`、scoped diff check 均 pass |
| Robot diagnostics metadata-only consumption | 通过 | diagnostics unittest 65 条 pass；文档记录不触发 collect/dropoff/cancel/ACK/cursor/Nav2/HIL/delivery success |
| Full-stack mobile/web 只读 panel | 通过 | mobile unittest 36 条 pass；`node --check` pass；panel 不改变 Start/Confirm/Cancel gating |
| `delivery_success=false` 与 `not_proven` 边界 | 通过 | 三端 required `rg` 均覆盖 boundary、not_proven、dropoff/cancel completion |
| 文档同步 | 通过 | `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 已由对应 worker 更新 |
| 真实手机/browser 补验 | 未完成 | `iab unavailable`，不计真实手机、真实 browser 或 PWA prompt/user choice 证明 |

## 3. OKR 对照

- Objective 2：completion signal 支持任务结果、dropoff/cancel completion status、failure/recovery reason 和 operator next steps 的软件复核，因此可保守 +1pp。
- Objective 3：固定路线材料、task record 和 same `evidence_ref` 状态被整理为 completion verdict，支持固定路线复核流程，因此可保守 +1pp。
- Objective 1：无 WAVE ROVER、UART、真实串口、`T=1001` feedback 或 HIL，保持不变。
- Objective 4：mobile/web 是只读 panel，未完成真实 iPhone/Android device behavior、production app 或 PWA prompt/user choice，保持不变。
- Objective 5：无公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration，保持不变。

## 4. 证据边界

本轮证据边界固定为 `software_proof_docker_route_task_completion_signal_gate`。

明确不是：

- 真实 Nav2/fixed-route 运行。
- 真实路线采集或关键帧实景证据。
- 真实 dropoff completion、cancel completion 或 delivery success。
- WAVE ROVER、真实串口/UART、`T=1001` feedback 或 HIL。
- 真实手机设备/browser、production app、真实 PWA prompt/user choice。
- Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

## 5. 验收结论

本 sprint 可作为 O2/O3 Docker/local completion signal 软件证据收口。下一轮若继续推进 O2/O3，必须走向真实 field-run 材料：真实 Nav2/fixed-route、同一 `evidence_ref` 上车实机复账、真实 dropoff/cancel completion 或 delivery success。若推进 O5，必须先拿真实外部材料，不能继续用本地 metadata depth 代替。
