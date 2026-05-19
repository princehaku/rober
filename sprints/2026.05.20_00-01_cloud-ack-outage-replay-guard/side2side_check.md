# Sprint 2026.05.20_00-01 Cloud ACK Outage Replay Guard - Side2Side Check

## 1. 验收结论

- sprint_type: epic
- Product 验收状态：通过 closeout 验收，可提交。
- 对照对象：`prd.md` 的 P0/P1 验收口径、`tech-plan.md` 的 owner/file scopes 和 Objective 5 边界。
- 证据边界：`software_proof_docker_cloud_ack_outage_replay_guard`。

## 2. PRD 对照

| PRD 要求 | 验收结果 | 证据 |
| --- | --- | --- |
| ACK POST 失败后 pending ACK 持久化，`last_terminal_ack_id` 不推进 | 通过 | `test_remote_bridge.py` 覆盖 outage state；`remote_bridge.py` 保存 `pending_terminal_ack` 并保持 cursor 不变。 |
| worker 重启后先补发 pending ACK | 通过 | `test_pending_ack_replays_after_restart_without_duplicate_local_execution` 覆盖 restart replay。 |
| replay 不重复执行本地命令 | 通过 | restart backend calls 为空，pending ACK replay 优先于拉取新 command。 |
| malformed ACK response 走同一保护 | 通过 | malformed ACK test 保存 pending ACK，下一轮补发并清理。 |
| pending ACK state redacted | 通过 | redaction test 排除 bearer、Authorization、`/cmd_vel`、WAVE ROVER、serial、baudrate、traceback、`delivery_success=true`。 |
| 产品文档同步 | 通过 | `docs/product/remote_4g_mvp.md` 新增 `cloud_ack_outage_replay_guard` 小节。 |
| 手机用户不被误导为 delivery success | 通过，只读 | Full-Stack worker 确认现有 mobile/web fail-closed copy 足够，本轮不改 UI。 |

## 3. OKR 对照

- Objective 5：本轮针对 command/status/ack 契约和 4G 中断 graceful degradation 的一个具体本地故障恢复 gap，但仍是 Docker/local `software_proof`，所以 Objective 5 保持约 68%。
- Objective 4：只读确认手机语义不把 pending ACK 写成 delivery success；没有真实手机/browser 验收，所以不调整进度。
- Objective 1/2/3：本轮没有硬件、Nav2/fixed-route、电梯、dropoff/cancel 或 HIL 材料，不调整进度。

## 4. 边界核对

本轮明确不证明：

- 真实 4G/SIM。
- 公网 HTTPS/TLS。
- OSS/CDN live traffic。
- production DB/queue。
- production worker/migration/cutover。
- 真实手机/browser。
- Nav2/fixed-route。
- WAVE ROVER / UART / HIL。
- delivery success。

PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，不得因本轮 closeout 关闭。

## 5. 责任人

- Robot Platform Engineer：实现和 targeted tests。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 copy / fail-closed 语义确认。
- Product Manager / OKR Owner：sprint closeout、OKR 4.1、`docs/process/okr_progress_log.md` 和提交推送。
