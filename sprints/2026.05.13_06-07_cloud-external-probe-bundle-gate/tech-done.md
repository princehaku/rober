# Sprint 2026.05.13_06-07 Cloud External Probe Bundle Gate - Tech Done

## Sprint 类型

- sprint_type: epic
- closeout owner: product-okr-owner
- 本轮证据边界：`software_proof_docker_cloud_external_probe_bundle_gate`
- 结论：工程 worker 已完成 external probe bundle gate 的 Docker/local 软件证明；该证明不等于真实云、真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue、HIL、Nav2/fixed-route、WAVE ROVER 或真实送达。

## 实际改动

### full-stack-software-engineer

改动文件：

- `.env.example`
- `cloud-relay/README.md`
- `cloud-relay/scripts/docker_smoke.sh`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`

交付内容：

- 新增 `trashbot.cloud_external_probe_bundle` schema_version=1。
- external probe 覆盖 `/healthz`、`/readyz`、`/preflightz`。
- artifact 明确输出 `evidence_boundary=software_proof_docker_cloud_external_probe_bundle_gate`、`production_ready=false`、`overall_status=blocked`。
- Docker smoke 增加 external probe artifact、preflight consumption、redaction checks、command/status/ack、backup restore、restart recovery 组合围栏。
- `.env.example`、`cloud-relay/README.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md` 同步 external probe 的配置占位、证据边界和非证明项。

关键 artifact 片段：

```json
{
  "schema": "trashbot.cloud_external_probe_bundle",
  "schema_version": 1,
  "evidence_boundary": "software_proof_docker_cloud_external_probe_bundle_gate",
  "production_ready": false,
  "overall_status": "blocked"
}
```

### robot-software-engineer

改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

交付内容：

- 新增 metadata-only `cloud_external_probe`、`cloud_external_probe_bundle`、deployment readiness、preflight response 兼容围栏。
- 证明上述 metadata-only response 不触发 backend action、不 POST ACK、不推进内存 cursor、不持久化 cursor。
- protocol normalization 继续剥离 command envelope 外的 external probe metadata，不把部署诊断数据升级为 `trashbot.remote.v1` robot command。
- `docs/interfaces/ros_contracts.md` 同步 cloud external probe 是 diagnostic/deployment metadata，不改变 ACK 语义。

## 验证结果

### full-stack validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 56 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
pass

cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
pass
probe covered /healthz http_status=200 status=pass
probe covered /readyz http_status=200 status=pass
probe covered /preflightz http_status=503 status=pass
cloud_external_probe_bundle status=pass
evidence_boundary=software_proof_docker_cloud_external_probe_bundle_gate
production_ready=false

scoped git diff --check
pass
```

### robot validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 66 tests in 33.399s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
pass

scoped git diff --check
pass
```

## 偏差和失败定位

- 未发现需要 Product Owner 退回工程 worker 重试的失败。
- 本轮没有运行 broad regression；验证按 tech-plan 采用 targeted unittest、`py_compile`、Docker smoke 和 scoped diff check。
- `overall_status=blocked` 是设计内结果：external probe bundle 已能稳定描述本地 Docker relay 的 endpoint contract，但真实生产入口和真实网络链路仍未补齐。

## 剩余风险

- 仍没有真实云主机、真实 HTTPS/TLS、公网入口、公网 DNS、防火墙实配或真实反向代理证据。
- 仍没有真实 4G/SIM、真实手机设备、production app、真实 PWA install prompt 或真实用户验收。
- 仍没有 OSS/CDN live traffic、production DB/queue、多实例一致性或 production disaster recovery。
- 仍没有 Nav2/fixed-route、WAVE ROVER、HIL、真实串口反馈或真实送达。
- ACK 仍只能解释为 command accepted/processing evidence，不能解释为 delivery success。
