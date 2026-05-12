# Sprint 2026.05.12_12-13 Remote OSS/CDN Phone Consumption Gate - Final

## 状态

- 阶段：final
- 收口时间：2026-05-12 13:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 证据边界：`software_proof_docker_phone_manifest_consumption`
- 收口结论：本轮完成 Product acceptance；建议并已在 `OKR.md` 保守上调 O6。

## 用户价值和产品北极星

本轮让普通手机用户和售后同学能在 operator 首屏、`/api/status.phone_readiness` 和 `/api/diagnostics` 中看到 phone-readable 诊断对象引用状态：`诊断对象引用已准备/缺失/损坏/过期`，并获得 retry hint。用户不需要看 raw manifest、bucket/key、checksum、ROS topic、串口参数或云密钥。

这直接服务北极星：手机是普通用户唯一入口，4G/云中转能力要让用户看得懂状态和恢复建议，而不是只留下工程 artifact。

## OKR 映射和进度判断

- O6 KR3：OSS/CDN manifest 不再只停留在 artifact/preflight 层，已进入 phone/API consumption gate。
- O6 KR4：CDN URL rule 摘要可被诊断和首屏消费，但仍不证明 CDN origin fetch。
- O6 KR5：凭证与敏感字段 redaction 边界保持，UI/API 不展示 secret、Authorization、AK/SK、root password、串口、ROS topic 或 `/cmd_vel`。
- O6 KR6：`missing/invalid/stale` 有 phone-safe safe summary 和 retry hint，形成 graceful degradation 的软件证据。

O6 进度判断：从约 36% 保守上调到约 38%。理由是本轮补齐了上一轮 O6 明确剩余缺口中的“正式手机 UI/API 消费 manifest 摘要”软件证明；但仍没有真实 OSS upload、STS、CDN origin fetch、真实云、真实 4G/SIM、HTTPS/TLS 公网或生产持久化证据，因此只能小幅上调，不进入真实云/生产可用口径。

## 本轮核心抓手

把 `software_proof_docker_oss_cdn_manifest` artifact 转成 `software_proof_docker_phone_manifest_consumption`：同一 manifest helper 被 status 和 diagnostics 消费，operator 首屏显示普通用户文案，异常状态给出安全恢复建议。

## 实际改动证据

Full-stack worker 已完成：

- `remote_cloud_relay.py`：新增 `build_phone_oss_cdn_manifest_summary()`，复用 manifest 校验规则并输出 phone-safe summary。
- `operator_gateway.py`：新增 `oss_cdn_manifest_artifact_ref` 配置入口。
- `operator_gateway_http.py`：`/api/status.phone_readiness.oss_cdn_manifest` 接入 summary，首屏显示诊断对象引用状态和 retry hint。
- `operator_gateway_diagnostics.py`：`/api/diagnostics.oss_cdn_manifest` 接入同一 helper。
- Targeted tests：扩展 operator HTTP、diagnostics、remote cloud relay 现有测试。
- Product docs：同步更新 `docs/product/mobile_user_flow.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`。
- Sprint docs：更新 `tech-done.md`。

Robot compatibility worker 已完成：

- 只读无改动。
- `remote_bridge` protocol/bridge compatibility fence 通过，确认 command/status/ack/cursor 语义未退化。

## 验证结果

Full-stack validation：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

结果：`Ran 62 tests in 16.283s OK`

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：`Ran 24 tests in 6.374s OK`

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

Robot compatibility validation：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

结果：`Ran 31 tests in 15.206s OK`；仅一次 `ResourceWarning`，不影响通过。

Scoped diff check：

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/product/mobile_user_flow.md \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/tech-done.md
```

结果：通过，无输出。

Product acceptance validation：

```bash
git diff --check -- \
  OKR.md \
  sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/side2side_check.md \
  sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/final.md
```

结果：通过，无输出。

## 做什么 / 不做什么

已做：

- phone/API manifest consumption gate。
- `ready/missing/invalid/stale` 用户可读摘要和 retry hint。
- status 和 diagnostics 共享 helper，减少口径漂移。
- operator 首屏显示诊断对象引用状态。
- 产品文档同步和 sprint 留档。

明确不做且未宣称：

- 真实 OSS upload、STS issuance、受限 AK、CDN origin fetch、生命周期策略、production account。
- 真实云部署、HTTPS/TLS 公网入口、真实 4G/SIM、carrier 弱网测试。
- 生产 DB/queue、多实例一致性、生产备份策略、真实灾备。
- 正式手机 app、真实手机设备/浏览器验收。
- Nav2/fixed-route 送达、WAVE ROVER、真实串口、T1001 feedback、HIL。

## 风险和下一步证据链

- 真实云与 4G：仍需公网 HTTPS/TLS、真实 4G/SIM、生产鉴权/rotate、弱网恢复和真实手机浏览器验收。
- OSS/CDN：仍需真实 OSS upload、STS/受限 AK、CDN origin fetch、生命周期策略和 production account。
- 生产可靠性：仍需生产 DB/queue、多实例一致性、生产备份策略和真实灾备。
- 机器人闭环：本轮不提升 O1/O2/O3/O4/O5，真实 Nav2/fixed-route、WAVE ROVER/HIL 和送达证据仍是独立缺口。

## 最终 Product 判断

本轮可收口。O6 可以从约 36% 保守上调到约 38%，但必须保持 `software_proof_docker_phone_manifest_consumption` 证据边界。下一轮 O6 若继续推进，应优先补真实云/公网 HTTPS/TLS 或真实 OSS upload + CDN 回源证据；若按全局最低完成度推进，O6 与 O5 将成为同一低位区间，需要结合真实手机验收和真实云通路选下一抓手。
