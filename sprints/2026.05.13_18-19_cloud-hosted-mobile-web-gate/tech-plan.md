# Sprint 2026.05.13_18-19 Cloud-hosted Mobile Web Gate - Tech Plan

## 目标

在不接入真实公网、4G/SIM、OSS/CDN 或 production DB/queue 的前提下，让 `cloud-relay` Docker/local runtime 托管 `mobile/web/` dependency-free PWA 静态壳，并补齐 robot-side protocol fence，证明静态 PWA GET 不触发 command/action/ACK/cursor。

证据边界命名为 `software_proof_docker_cloud_hosted_mobile_web_gate`。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 67%。
2. 本 sprint 是否针对最低 Objective：是。本轮直接推进 O5 的 cloud-relay phone web shell 入口，把正式手机入口从独立静态文件推向 cloud-relay same-origin 托管。
3. 支撑关系：本 sprint 同时支撑 Objective 4 手机用户体验，但不因 Docker/local proof 冒充真实云、真实公网 TLS、真实 4G、真实手机设备/browser、production app、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。上一轮 external evidence intake gate 已完成但没有真实外部材料，本轮避免继续重复 metadata-only 深度。

## 并行执行计划

### Task A - full-stack-software-engineer

本轮任务：

- 在 `cloud-relay` runtime 中实现 static PWA serving gate，服务 `mobile/web/` dependency-free 静态壳。
- 保持 `/api/*`、`/robots/*`、`/healthz`、`/readyz`、`/preflightz` 等 API/probe 路由优先，静态 fallback 不覆盖控制面。
- 更新 cloud-relay docs、mobile docs 和相关产品文档，写清运行方式、证据边界和非声明。

允许改动文件范围：

- `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/mobile_user_flow.md`
- `mobile/README.md`
- 必要时新增或更新 cloud-relay 侧 targeted unittest/smoke 文件，但不得改 robot bridge compatibility tests。

接口影响：

- 新增或确认静态 GET 入口，例如 `/`、`/index.html`、PWA assets、`/manifest.webmanifest`、`/service-worker.js`、`/offline.html`。
- 不改变 `trashbot.remote.v1` command/status/ack schema。
- 不新增 raw ROS topic、`/cmd_vel`、serial、WAVE ROVER、credential、DB/queue URL 暴露。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
bash cloud-relay/scripts/docker_smoke.sh
git diff --check -- cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md mobile/README.md onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

输出要求：

- 返回实际改动文件列表。
- 返回 PWA GET、API/probe 路由和 Docker/local smoke 结果。
- 明确失败定位和剩余风险。

### Task B - robot-software-engineer

本轮任务：

- 补 remote bridge/protocol compatibility fence，证明静态 PWA GET 或 hosted PWA metadata 不触发 robot command/action/ACK/cursor。
- 证明 metadata-only 或 static-shell-only 响应不调用 `collect`、`confirm_dropoff`、`cancel`，不 POST ACK，不推进 in-memory `last_ack_id`，不持久化 `last_terminal_ack_id`。
- 更新 ROS/remote contract 文档，说明 cloud-hosted PWA 是 phone/static surface，不扩大 robot command envelope。

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- 必要时仅为通过 compatibility fence 更新 robot bridge normalization 相关最小代码；若需要改产品代码，必须在返回中说明具体理由和风险。

接口影响：

- 不改变可执行 command type。
- 不改变 ACK terminal semantics。
- 不改变 cursor persistence 规则。
- 新增 metadata ignore/strip 规则只用于防止 hosted PWA/static-shell 字段污染 command envelope。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

输出要求：

- 返回实际改动文件列表。
- 返回 compatibility fence 测试输出，特别标明 command/action/ACK/cursor 未触发。
- 返回失败定位和剩余风险。

## 集成验收

两个 Task 返回后，由主节点或 `product-okr-owner` 只做验收与留档：

- 核对 Task A 的 PWA GET 证据与 Task B 的 robot protocol fence 是否一致。
- 更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 仅在证据支持时更新 `OKR.md`；若仍只是 Docker/local software proof，应保持 O5 进度谨慎，不因本地托管壳虚增。
- 如完成 durable docs/code，需要提交并推送，排除 unrelated worktree churn。

## 风险边界

- 本 sprint 不证明真实云、公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、真实手机设备/browser、production app、PWA install prompt、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK、HTTP accepted、页面可打开、Docker smoke 均不是 delivery success。
- 若 Docker/local smoke 因环境失败，必须定位为环境或实现问题，不得改写为真实云阻塞证据。

## Product closeout 后续文档

后续必须补：

- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/tech-done.md`
- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/side2side_check.md`
- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/final.md`

后续可能更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`
