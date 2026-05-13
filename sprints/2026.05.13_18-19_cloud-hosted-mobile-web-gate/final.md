# Sprint 2026.05.13_18-19 Cloud-hosted Mobile Web Gate - Final

## Sprint 类型

- `sprint_type: epic`
- 收口时间：2026-05-13 19:00 Asia/Shanghai
- 主目标：Objective 5 云中转 + OSS/CDN 数据通路产品化
- 支撑目标：Objective 4 手机用户体验与低成本量产边界
- 证据边界：`software_proof_docker_cloud_hosted_mobile_web_gate`

## 用户价值和产品北极星

本轮把“手机用户只有一个云中转入口”的产品形态向前推进：`cloud-relay` Docker/local runtime 现在可以 same-origin 托管 `mobile/web/` PWA 静态壳，并提供 phone-safe/fail-closed `/api/status`、`/api/diagnostics` adapter。用户未来打开云中转根路径即可进入同一份 PWA，而不是理解独立静态目录或本地文件服务。

这仍是 Docker/local software proof，不是 production app、真实公网、真实手机设备或真实送达。

## 本轮核心抓手

核心抓手是 cloud-hosted mobile web gate：

- Task A 让 `cloud-relay` 托管 PWA 静态入口，并保证 API/probe/control route 不被 fallback 覆盖。
- Task A 同步补 phone-safe fail-closed status/diagnostics adapter。
- Task B 补 robot compatibility fence，证明 hosted PWA/static-shell metadata 不触发机器人动作、ACK 或 cursor。
- Product closeout 将 O5 进度从约 67% 谨慎调整到约 68%，O4 保持约 70%。

## 实际交付

Task A Full-stack：

- cloud-relay 托管 `mobile/web/` PWA at `/`、`/index.html`、`/app.js`、`/styles.css`、`/manifest.webmanifest`、`/service-worker.js`、`/offline.html` 和 icons。
- Dockerfile 已 `COPY mobile/web /app/mobile/web`。
- API/probe/control route 不被 static fallback 覆盖。
- 新增免 bearer、phone-safe、fail-closed `GET /api/status` 和 `GET /api/diagnostics` adapter。
- 默认 robot id 为 `TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID` 或 `trashbot-001`。
- 缺 status 返回 blocked/missing，不再 404；有 status 只复制 safe fields。
- `can_collect=false`、`can_confirm_dropoff=false`、`can_cancel=false`、`phone_readiness.can_continue=false`、`command_safety.actions.*.enabled=false`。
- 不改变 `/robots/{robot_id}/status`、command、ACK 的 `trashbot.remote.v1` robot contract。

Task B Robot：

- 只补 compatibility fence 和 `docs/interfaces/ros_contracts.md`，未改生产代码。
- `cloud_hosted_pwa`、`static_shell_metadata`、`pwa_static_surface`、`cloud_hosted_mobile_web_gate` metadata-only 不触发 collect/confirm_dropoff/cancel。
- metadata-only 不 POST ACK、不推进 in-memory `last_ack_id`、不持久化 `last_terminal_ack_id`。
- valid collect command mixed metadata 只执行 command envelope。
- ACK/status 不带 static metadata、delivery_success、cursor_override、Authorization、`/cmd_vel`。

## 验证结果

```text
Task A:
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 72 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
OK

bash cloud-relay/scripts/docker_smoke.sh
OK
覆盖：镜像构建、health/ready、preflight blocked-by-design、status/command/ack、backup/restore、restart recovery。
readiness 等待期间一次连接重置后自动重试成功。

Task B:
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 100 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
OK

Task A/B scoped git diff --check
OK
```

Product closeout 另执行并通过：

```text
test -f .../tech-done.md && test -f .../side2side_check.md && test -f .../final.md
exit 0

rg -n "software_proof_docker_cloud_hosted_mobile_web_gate|Objective 5|约 68%|ACK" OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate
matched OKR.md, docs/process/okr_progress_log.md, tech-done.md, side2side_check.md, final.md, pre_start.md, prd.md, tech-plan.md

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate
exit 0
```

## OKR 更新

- Objective 5：约 67% -> 约 68%。
- 调整理由：正式手机入口与云中转控制面形成 same-origin Docker/local proof；`cloud-relay` 托管 PWA 静态壳，同时提供 fail-closed phone API adapter，并有 robot compatibility fence 防止静态/metadata surface 污染 command/ACK/cursor。
- Objective 4：保持约 70%。本轮支撑手机体验，但没有真实手机设备/browser、production app 或真实 PWA install prompt。
- Objective 1/2/3：不调整。

## 风险、阻塞和证据缺口

仍缺：

- 真实公网 HTTPS/TLS。
- 真实 4G/SIM。
- 真实手机设备/browser。
- production app。
- 真实 PWA install prompt。
- OSS/CDN live traffic。
- production DB/queue。
- Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

ACK 仍只是 accepted/processing evidence，不是 delivery success。

## 下一步建议

Objective 5 仍是最低完成度。下一轮若能获得外部环境，应优先接入真实 HTTPS/TLS 公网入口、4G/SIM、OSS/CDN live traffic 或 production DB/queue connectivity，并把这些材料接入现有 external evidence intake/preflight 链路。若外部环境仍不可用，则应转向 Objective 4 的真实手机设备/browser、production app 或 PWA install prompt 验收，避免继续重复本地 metadata 深度。
