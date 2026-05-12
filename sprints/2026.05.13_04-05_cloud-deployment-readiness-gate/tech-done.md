# Sprint 2026.05.13_04-05 Cloud Deployment Readiness Gate - Tech Done

## Sprint Type

- sprint_type: epic
- Evidence boundary target: `software_proof_docker_cloud_deployment_readiness_gate`

## Product 北极星和用户价值

本轮的用户价值是让云中转从"本地 relay 可跑"推进到"上线前缺口可机器读取、可审计、可交接"。普通手机用户未来依赖云端入口控制小车；工程和运维必须能清楚看到当前还缺真实云、TLS、公网入口、4G/SIM、生产 DB/queue、OSS/CDN 实流量等外部证据，不能把 Docker smoke 当成 production ready。

产品北极星保持不变：phone web/app -> cloud API -> robot outbound polling -> ROS2 behavior。本轮只完成 Docker/local deployment readiness gate，不声明真实云、真实生产链路或真实送达。

## OKR 映射与 KR 拆解

- Objective 5 KR1/KR2：preflight 暴露 cloud deployment readiness gate，覆盖 public URL/TLS/ingress、healthcheck、bearer placeholder、state backend 和云端部署缺口。
- Objective 5 KR3/KR4：OSS/CDN 仍进入 readiness gate，但只作为本地配置和缺口检查，不证明真实上传、CDN 回源或 live traffic。
- Objective 5 KR5：`.env.example` 只放占位符；preflight 和 artifact 不泄漏 bearer token、Authorization、OSS AK/SK、DB/queue URL 或 credential-bearing URL。
- Objective 5 KR6：4G/SIM、生产 DB/queue、OSS/CDN、真实云配置缺失时保持 blocked/warning，避免手机或运维误判为可交付。
- Objective 2 guardrail：deployment readiness metadata 只作为诊断元数据，不触发 robot action、ACK、cursor 变化或 delivery success。

## Full-stack Worker Result

实际改动：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`。
- 更新 `cloud-relay/scripts/docker_smoke.sh`。
- 更新 `cloud-relay/README.md`。
- 更新 `.env.example`。
- 更新 `docs/product/cloud_4g_infrastructure.md`。
- 更新 `docs/product/remote_4g_mvp.md`。

实现结果：

- Implemented `trashbot.cloud_deployment_readiness` schema_version=1。
- Keeps `production_ready=false` / `overall_status=blocked`。
- Covers public URL/TLS/ingress, healthcheck, bearer credential placeholder, state backend, production DB/queue, OSS/CDN, 4G/SIM, runbook/smoke presence。
- Preflight exposes deployment-readiness gate without leaking credentials, raw paths, ROS topics, `/cmd_vel`, serial details, or tracebacks。

验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - `Ran 54 tests ... OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 退出码 0。
- `cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh`
  - 退出码 0。
  - `/preflightz` returned blocked with `software_proof_docker_cloud_deployment_readiness_gate`。
  - Artifact stayed `production_ready=false`。
  - command/status/ack and SQLite restart recovery still worked。
- `git diff --check -- <full-stack-touched-files>`
  - 退出码 0。

剩余风险：

- 仍未证明 real cloud、real HTTPS/TLS、public ingress、real 4G/SIM、OSS/CDN live traffic、production DB/queue、multi-instance consistency、production disaster recovery、real phone app/device、HIL、Nav2/fixed-route、WAVE ROVER 或 real delivery。
- 当前 evidence boundary 只能写为 `software_proof_docker_cloud_deployment_readiness_gate`。

## Robot Worker Result

实际改动：

- 更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`。
- 更新 `docs/product/remote_4g_mvp.md`。

实现结果：

- Added metadata-only deployment readiness fence proving `deployment_readiness` / `cloud_deployment_readiness` / `preflight` responses do not trigger robot backend calls, ACK posts, cursor advancement, or cursor persistence。
- Added protocol fence proving deployment readiness metadata outside the command envelope is stripped from normalized `trashbot.remote.v1` command。
- Added robot-side product contract wording that deployment readiness metadata is diagnostic only。
- No production runtime code was changed by robot worker; existing bridge behavior already satisfied the contract。

验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - `Ran 62 tests in 31.164s OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
  - 退出码 0。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/product/remote_4g_mvp.md`
  - 退出码 0。

剩余风险：

- Metadata-only fence 证明 robot 不误执行部署诊断元数据；它不证明任务闭环、Nav2/fixed-route、HIL、WAVE ROVER 或真实送达。
- ACK 仍只能解释为 command accepted/processing evidence，不能解释为 delivery success。

## Product Closeout

实际收口改动：

- 更新 `OKR.md`：最新 sprint 改为 `2026.05.13_04-05_cloud-deployment-readiness-gate`，Objective 5 从约 55% 保守上调到约 57%，Objective 1/2/3/4 不调整。
- 更新 `docs/process/okr_progress_log.md`：追加本轮证据、worker 验证和非证明项。
- 创建本文件、`side2side_check.md`、`final.md`。

Product 收口验证：

- `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`cloud-relay/README.md` 路径均已验证存在。
- 本轮 Product closeout 不改产品代码、测试代码、`.env.example`、`docs/product/*` 或 `cloud-relay/*`。

## 未完成事项与风险

- real cloud、real HTTPS/TLS、public ingress、real 4G/SIM、OSS/CDN live traffic、production DB/queue、multi-instance consistency、production disaster recovery、real phone app/device、HIL、Nav2/fixed-route、WAVE ROVER、real delivery 均未完成。
- `software_proof_docker_cloud_deployment_readiness_gate` 只能作为上线前 blocked readiness 证据，不可升级为 production ready。
- commit/push 尚未由本 Product closeout 执行，等待主会话最终检查后处理。
