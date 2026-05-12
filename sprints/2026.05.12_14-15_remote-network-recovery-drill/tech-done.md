# Sprint 2026.05.12_14-15 Remote Network Recovery Drill - Tech Done

## 状态

- 阶段：tech-done
- 主目标：O6 `software_proof_docker_network_recovery_drill`
- 证据边界：Docker/local software proof only

## Full-stack Relay Network Recovery Drill

### 实际改动

- `remote_cloud_relay.py` 新增 `--network-recovery-drill` 和 `--write-network-recovery-artifact`，生成 `schema=trashbot.network_recovery_drill`、`schema_version=1`、`evidence_boundary=software_proof_docker_network_recovery_drill` 的脱敏 artifact。
- Drill 覆盖本地等价 relay/cloud connection failure、ACK post failure 不等于 delivery success、恢复后 command/status/ack envelope 对账、status stale phone-safe blocked/warning。
- `--preflight` 新增 `TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT` 消费：missing 为 warning，invalid/stale/failed 为 blocked，passed 只设置 `software_proof_ready=true`，不声明 `production_ready`。
- `operator_gateway_http.py` 和 `operator_gateway_diagnostics.py` 新增 phone-safe network recovery summary：`phone_readiness.network_recovery` 与 `diagnostics.network_recovery_drill` 只显示摘要、retry hint、not_proven，不返回 full steps、路径、端口、traceback、credential、ROS topic、硬件字段或 checksum。
- `docs/product/remote_4g_mvp.md` 与 `docs/product/cloud_4g_infrastructure.md` 同步 network recovery drill、artifact、preflight、diagnostics 和 phone-safe consumption 口径。

### 接口影响

- 新增 CLI：
  - `python3 -m ros2_trashbot_behavior.remote_cloud_relay --network-recovery-drill --state-backend sqlite --state-path <sqlite> --write-network-recovery-artifact <json>`
  - `TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT=<json> python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight`
- 新增 preflight check：`network_recovery_drill`。
- 新增 phone/API 摘要字段：
  - `/api/status.phone_readiness.network_recovery`
  - `/api/diagnostics.network_recovery_drill`

### 当前验证结果

- Full-stack targeted unittest：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest ...` 输出 `Ran 93 tests in 23.778s OK`。
- `py_compile`：`remote_cloud_relay.py`、`operator_gateway_http.py`、`operator_gateway_diagnostics.py` 编译通过。
- CLI network recovery drill：输出 `ok=true`、`network_recovery_status=passed`、`evidence_boundary=software_proof_docker_network_recovery_drill`、`step_count=4`、`cursor_invariant.ack_failure_advances_cursor=false`、`cursor_invariant.ack_is_delivery_success=false`。
- CLI preflight consumption：输出 `network_recovery_drill=pass`、`software_proof_ready=true`、`production_ready=false`、`overall_status=blocked`、`evidence_boundary=software_proof_docker_network_recovery_drill`；blocked 项仍来自缺生产 credential/TLS/public ingress/OSS/CDN/state store，不提升真实云/4G。
- scoped `git diff --check`：通过。

### 剩余风险

- 本段只证明 Docker/local relay recovery artifact 和 phone-safe consumption，不证明真实云、真实 4G/SIM、HTTPS/TLS、公网入口、生产 DB/queue、多实例一致性、生产 incident recovery、真实 OSS/CDN 流量、正式手机 app、真实手机设备验收、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只表示 command envelope accepted/processing evidence，不代表 delivery success。

## Robot Bridge Compatibility Fence

### 实际改动

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py` 补齐 network recovery compatibility fence，覆盖 malformed status response、malformed ACK response、ACK post failure 和恢复后同一 command terminal ACK 缓存重发语义。
- `docs/product/remote_4g_mvp.md` 同步 Robot bridge / cursor network recovery 口径，明确 remote_bridge 在不可确认响应下保持保守：不触发本地 action、不推进 cursor、不持久化 terminal cursor。
- `remote_bridge.py` 现有实现已满足上述保守语义，本轮未改产品代码。

### 当前验证结果

- Robot targeted unittest：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py` 输出 `Ran 33 tests in 16.192s OK`。
- `py_compile`：`src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py` 编译通过。
- scoped `git diff --check`：通过。

### 语义验收

- malformed status response 与 malformed ACK response 不触发本地 action、不落 cursor。
- ACK 响应不可信时不落 cursor。
- 恢复后同一 command 只重发缓存 terminal ACK，不重复触发本地 action。

### 剩余风险

- 本段只证明 remote_bridge command/status/ack/cursor 保守语义的软件围栏，不证明真实云、真实 4G/SIM、生产网络恢复、多实例一致性、真实 ROS2 action 执行、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## Product Integration Closeout

### 用户价值和产品北极星

- 用户价值：普通手机/operator 用户在断网、ACK 失败、status stale 或恢复演练缺失/损坏/过期时，可以看到保守的网络恢复状态，而不是误以为 command 已送达或任务已完成。
- 产品北极星：正式 4G 链路仍是 `phone web/app -> cloud HTTPS API -> robot remote_bridge outbound polling -> ROS2 behavior`；本轮只证明 Docker/local 弱网恢复语义和 phone-safe 摘要，不改变真实云、真实手机或机器人实机验收边界。

### OKR 映射和 KR 拆解

- O6 KR6：完成 `software_proof_docker_network_recovery_drill`，覆盖 4G 中断类 graceful degradation 的 Docker/local drill、artifact、preflight/diagnostics 消费和 robot bridge cursor 保守语义。
- O6 KR1/KR5：command/status/ack 继续保持 envelope-only 和凭证/内部细节脱敏，不暴露 `/cmd_vel`、ROS topic、串口、WAVE ROVER 字段、路径或 credential。
- O5：只记录 phone-safe readiness/diagnostics 支撑，不作为本轮主目标上调。
- O1/O2/O3/O4：本轮无真实串口、HIL、Nav2/fixed-route、相机实景或送达证据，不上调。

### 优先级和验收口径

- P0 已满足：Full-stack drill artifact、preflight consumption、phone-safe diagnostics summary、Robot bridge compatibility fence、targeted unittest、py_compile 和 scoped diff check 均有工程 owner 回填证据。
- P1 已满足：`/api/status.phone_readiness.network_recovery` 与 `/api/diagnostics.network_recovery_drill` 可消费 network recovery summary，并保持 `not_proven` / retry hint 口径。
- 不验收：真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、生产鉴权/rotate、STS/受限 AK、真实 OSS upload、CDN origin fetch、生产 DB/queue、多实例一致性、正式手机 app/真实手机设备验收、Nav2/fixed-route、WAVE ROVER、HIL、真实送达。

### 责任 Engineer

- `full-stack-software-engineer`：Task A relay drill、artifact、preflight、diagnostics、phone-safe summary 和相关 docs。
- `robot-software-engineer`：Task B remote_bridge compatibility fence、cursor/ACK 保守语义和相关 docs。
- `product-okr-owner`：Task C 集成验收、sprint 收口、OKR 进度快照更新。

### Product 验收命令

- 已运行并通过：`git diff --check -- sprints/2026.05.12_14-15_remote-network-recovery-drill/tech-done.md sprints/2026.05.12_14-15_remote-network-recovery-drill/side2side_check.md sprints/2026.05.12_14-15_remote-network-recovery-drill/final.md OKR.md`
