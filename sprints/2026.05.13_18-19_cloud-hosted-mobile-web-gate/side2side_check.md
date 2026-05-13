# Sprint 2026.05.13_18-19 Cloud-hosted Mobile Web Gate - Side-by-side Check

## Sprint 类型

- `sprint_type: epic`
- 检查时间：2026-05-13 18:58 Asia/Shanghai
- 证据边界：`software_proof_docker_cloud_hosted_mobile_web_gate`

## 产品验收结论

本轮 Product 验收通过，可以进入 `final.md` 收口。Task A/B 共同证明：`cloud-relay` Docker/local runtime 可以托管 `mobile/web/` PWA 静态壳，同时保持 `/api/*`、probe/control route 和 `trashbot.remote.v1` robot contract 不被静态 fallback 污染；robot compatibility fence 证明 hosted PWA/static-shell metadata 不触发机器人动作、ACK 或 cursor 推进。

这给 Objective 5 一个小幅实质推进：正式手机入口与云中转控制面形成 same-origin Docker/local proof。Objective 5 可从约 67% 保守调整到约 68%。Objective 4 只记录支撑，不上调。

## Side-by-side 对照

| 预期 | 实际 | 验收 |
| --- | --- | --- |
| cloud-relay 托管 `mobile/web/` 静态壳 | Task A 完成 `/`、`/index.html`、`/app.js`、`/styles.css`、`/manifest.webmanifest`、`/service-worker.js`、`/offline.html` 和 icons 托管 | 通过 |
| Docker/local runtime 包含 PWA 静态资产 | Dockerfile 已 `COPY mobile/web /app/mobile/web` | 通过 |
| API/probe/control route 不被 static fallback 覆盖 | Docker smoke 覆盖 health/ready、preflight、status/command/ack、backup/restore、restart recovery | 通过 |
| `/api/status` 和 `/api/diagnostics` phone-safe/fail-closed | 新 adapter 免 bearer；缺 status 返回 blocked/missing；safe fields copy；主操作全 false | 通过 |
| 不改变 robot contract | 不改 `/robots/{robot_id}/status`、command、ACK 的 `trashbot.remote.v1` contract | 通过 |
| hosted PWA/static metadata 不触发机器人动作 | Task B fence 证明 metadata-only 不触发 collect/confirm_dropoff/cancel | 通过 |
| hosted PWA/static metadata 不触发 ACK/cursor | Task B fence 证明不 POST ACK、不推进 `last_ack_id`、不持久化 `last_terminal_ack_id` | 通过 |
| valid command mixed metadata 仍只执行 command envelope | Task B fence 证明 ACK/status 不带 static metadata、delivery_success、cursor_override、Authorization、`/cmd_vel` | 通过 |

## OKR 最低优先级回顾

启动时最低 Objective 是 Objective 5，约 67%。本 sprint 直接针对 O5：把 cloud relay 从纯 API/relay runtime 推进为可 same-origin 托管 phone PWA 的 Docker/local 入口，并补齐 fail-closed phone API adapter 与 robot compatibility fence。

收口后：

- Objective 5：约 67% -> 约 68%。
- Objective 4：保持约 70%，只记录 same-origin PWA 托管对手机体验的支撑。
- Objective 1/2/3：不调整。

## 证据链

- Task A Full-stack：`test_remote_cloud_relay.py` 72 tests OK；py_compile OK；`bash cloud-relay/scripts/docker_smoke.sh` OK；diff check OK。
- Task B Robot：remote bridge/protocol tests `Ran 100 tests ... OK`；py_compile OK；diff check OK。
- Product closeout：本文件、`tech-done.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 更新后执行文档围栏命令。

## 非声明边界

本轮不是：

- 真实公网 HTTPS/TLS。
- 真实 4G/SIM。
- 真实手机设备/browser 或真实 PWA install prompt。
- production app。
- OSS/CDN live traffic。
- production DB/queue。
- Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

ACK 仍只是 accepted/processing evidence，不是 delivery success。

## 剩余风险

- 真实公网/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic 仍缺，O5 仍是最低 Objective。
- 真实手机设备/browser、production app 和真实 PWA install prompt 仍缺，O4 不因本轮 Docker/local 托管而上调。
- 当前 `GET /api/status` / `GET /api/diagnostics` adapter 是 phone-safe/fail-closed 读接口，不代表 command path 可用于真实用户发车。
