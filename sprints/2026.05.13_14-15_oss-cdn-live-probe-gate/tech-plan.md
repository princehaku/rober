# Sprint 2026.05.13_14-15 OSS/CDN Live Probe Gate - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective：Objective 5，约 65%。
2. 本 sprint 针对该最低 Objective。
3. 具体理由：Objective 5 仍缺真实云、4G、OSS/CDN live traffic 和 production DB/queue 外部证据；上一轮 Objective 4 已上调到约 66%，Objective 5 成为最低。当前主机只有 Docker，因此本轮把 OSS/CDN live traffic 缺口推进成可执行 live probe gate，但不声明真实 OSS/CDN 已完成。

## Team 分工

### Task A - Full-stack OSS/CDN Live Probe Gate

Owner：`full-stack-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`

要求：

- 增加 `trashbot.oss_cdn_live_probe` schema v1、artifact writer、summary validator 和 preflight consumption。
- CLI 支持 `--write-oss-cdn-live-probe-artifact`、`--oss-cdn-live-probe-artifact`，环境变量支持 `TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT`。
- 生成 artifact 时可以复用现有 OSS/CDN manifest artifact；live probe 只保存 safe enum/status、object count、endpoint path 或 object key hash/摘要，不保存 token、header、完整 credential URL、本地路径或响应体。
- 当前 Docker-only proof 必须保持 `production_ready=false`、`overall_status=blocked`，即使本地 mock HTTP probe 通过也不得声明真实 CDN。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md
```

### Task B - Robot Metadata Compatibility Fence

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

要求：

- 增加 `oss_cdn_live_probe` / `oss_cdn_live_probe_artifact` / `cdn_live_probe` metadata-only compatibility fence。
- 证明这些字段不会触发 collect/dropoff/cancel，不 POST ACK，不推进内存 cursor，不持久化 `last_terminal_ack_id`。
- 接口文档说明它们只属于 phone/support metadata，不属于 command/status/ACK envelope。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

### Task C - Product Closeout

Owner：`product-okr-owner`

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_14-15_oss-cdn-live-probe-gate/tech-done.md`
- `sprints/2026.05.13_14-15_oss-cdn-live-probe-gate/side2side_check.md`
- `sprints/2026.05.13_14-15_oss-cdn-live-probe-gate/final.md`

要求：

- 等 Task A/B 返回后，基于实际证据更新 closeout。
- 仅在 full-stack gate 与 robot compatibility fence 都完成时，保守上调 Objective 5。
- 明确本轮不是真实 OSS/CDN live traffic、真实云、真实 4G/SIM、production DB/queue、HIL 或真实送达证据。

验收命令：

```bash
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_14-15_oss-cdn-live-probe-gate
```

## 接口影响

- 新增 readiness/preflight metadata，不改变 `trashbot.remote.v1` command/status/ACK 主 envelope。
- ACK 语义不变：只表示 command envelope accepted/processing，不表示 delivery success。

## 风险边界

- 当前没有真实 OSS/CDN 凭证或公网入口，不能产生真实 live traffic 证明。
- 本轮只能形成 Docker/local software proof，并为未来真实云环境提供可复用执行入口。
