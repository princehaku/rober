# Sprint 2026.05.13_18-19 Cloud-hosted Mobile Web Gate - Tech Done

## Sprint 类型

- `sprint_type: epic`
- Product closeout 时间：2026-05-13 18:55 Asia/Shanghai
- 证据边界：`software_proof_docker_cloud_hosted_mobile_web_gate`

## 用户价值和产品北极星

本轮把普通手机用户的正式入口向云中转靠近一步：同一份 `mobile/web/` PWA 不再只作为独立静态目录验证，而是由 `cloud-relay` Docker/local runtime same-origin 托管。产品北极星仍是让用户只通过手机入口查看状态、诊断和恢复建议，不接触 SSH、ROS2、串口、本地文件或机器人网络细节。

本轮不是 production app 或真实公网验收；它证明 cloud relay 控制面可以同时承载 phone web shell 和 phone-safe API，并且打开页面不会变成机器人动作。

## OKR 映射

- Objective 5 KR1：`cloud-relay` 继续保持 `trashbot.remote.v1` command/status/ack 契约，不暴露 `/cmd_vel`，不接受 inbound 直连小车；PWA 静态托管不覆盖 API/probe/control route。
- Objective 5 KR2：Docker/local `cloud-relay` 现在具备托管 phone web shell 的入口形态，支撑后续真实公网/HTTPS/TLS 部署验收。
- Objective 5 KR6：新增免 bearer、phone-safe、fail-closed `GET /api/status` 和 `GET /api/diagnostics` adapter，缺 status 返回 blocked/missing，不再 404；所有主操作默认 fail closed。
- Objective 4 KR1/KR5/KR7：同一份 `mobile/web/` 手机壳可由云中转入口消费，支撑手机体验，但不构成真实手机设备/browser、production app 或真实 PWA install prompt 证据。

## KR 拆解或更新

- O5 KR1 子证据：`/`、`/index.html`、`/app.js`、`/styles.css`、`/manifest.webmanifest`、`/service-worker.js`、`/offline.html` 和 icons 由 `cloud-relay` 托管，API/probe/control route 不被 static fallback 覆盖。
- O5 KR2 子证据：Dockerfile 已 `COPY mobile/web /app/mobile/web`，Docker smoke 覆盖镜像构建、health/ready、preflight、status/command/ack、backup/restore 和 restart recovery。
- O5 KR6 子证据：`/api/status` 和 `/api/diagnostics` adapter 默认 robot id 来自 `TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID` 或 `trashbot-001`；缺 status 时返回 blocked/missing，有 status 时只复制 safe fields。
- Robot compatibility 子证据：`cloud_hosted_pwa`、`static_shell_metadata`、`pwa_static_surface`、`cloud_hosted_mobile_web_gate` metadata-only 不触发 collect/confirm_dropoff/cancel，不 POST ACK，不推进 in-memory `last_ack_id`，不持久化 `last_terminal_ack_id`。

## 实际改动

### Task A - full-stack-software-engineer

实际完成：

- `cloud-relay` 托管 `mobile/web/` PWA at `/`、`/index.html`、`/app.js`、`/styles.css`、`/manifest.webmanifest`、`/service-worker.js`、`/offline.html` 和 icons。
- Dockerfile 增加 `COPY mobile/web /app/mobile/web`。
- API/probe/control route 不被 static fallback 覆盖。
- 新增免 bearer、phone-safe、fail-closed `GET /api/status` 和 `GET /api/diagnostics` adapter；默认 robot id 为 `TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID` 或 `trashbot-001`。
- 缺 status 返回 blocked/missing，不再 404；有 status 时只复制 safe fields。
- `can_collect=false`、`can_confirm_dropoff=false`、`can_cancel=false`、`phone_readiness.can_continue=false`、`command_safety.actions.*.enabled=false`。
- 不改变 `/robots/{robot_id}/status`、command、ACK 的 `trashbot.remote.v1` robot contract。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 72 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
OK

bash cloud-relay/scripts/docker_smoke.sh
OK
覆盖：镜像构建、health/ready、preflight blocked-by-design、status/command/ack、backup/restore、restart recovery。
备注：readiness 等待期间出现一次连接重置，脚本自动重试后成功。

git diff --check -- Task A touched files
OK
```

### Task B - robot-software-engineer

实际完成：

- 只补 compatibility fence 和 `docs/interfaces/ros_contracts.md`，未改生产代码。
- 证明 `cloud_hosted_pwa`、`static_shell_metadata`、`pwa_static_surface`、`cloud_hosted_mobile_web_gate` metadata-only 不触发 collect/confirm_dropoff/cancel。
- 证明 metadata-only 不 POST ACK、不推进 in-memory `last_ack_id`、不持久化 `last_terminal_ack_id`。
- valid collect command mixed metadata 只执行 command envelope。
- ACK/status 不带 static metadata、delivery_success、cursor_override、Authorization、`/cmd_vel`。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 100 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
OK

git diff --check -- Task B touched files
OK
```

## 验收口径对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Docker/local cloud-relay 返回 PWA 静态入口 | 通过 | Task A hosted `/`、HTML、JS、CSS、manifest、service worker、offline shell 和 icons。 |
| `/api/status`、`/api/diagnostics` 保持 phone-safe JSON | 通过 | 新 adapter fail-closed；缺 status blocked/missing；有 status 只复制 safe fields。 |
| 静态托管不吞掉 API/probe/control route | 通过 | Task A 明确 API/probe/control route 不被 static fallback 覆盖，Docker smoke 通过。 |
| 静态/metadata-only 不触发 command/action/ACK/cursor | 通过 | Task B remote bridge/protocol fence `Ran 100 tests ... OK`。 |
| Robot command/status/ACK envelope 未扩大 | 通过 | valid command mixed metadata 只执行 command envelope，ACK/status 不带 static metadata。 |
| 文档同步 | 通过 | Task A/B 已同步 cloud-relay/mobile/product/interface 相关文档；Product 本轮补齐 sprint closeout、OKR 和进度日志。 |

## 偏差

- 原计划强调 cloud-relay static PWA serving gate；Task A 额外补了 `GET /api/status` 和 `GET /api/diagnostics` adapter。该补充符合 O5/O4 用户价值，因为 same-origin PWA 需要 phone-safe 读接口；同时保持 fail-closed，未改变 robot contract。
- 本轮未接入真实外部材料，未解决公网/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue 缺口。

## 剩余风险

- 这只是 `software_proof_docker_cloud_hosted_mobile_web_gate`。
- 不是真实公网 HTTPS/TLS、真实 4G/SIM、真实手机设备/browser、production app、真实 PWA install prompt、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
