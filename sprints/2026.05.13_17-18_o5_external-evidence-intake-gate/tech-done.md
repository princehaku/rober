# Sprint 2026.05.13_17-18 O5 External Evidence Intake Gate - Tech Done

## sprint_type

epic

## 实际改动

Task A Full-stack 完成 O5 external evidence intake gate：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`

新增 `trashbot.external_evidence_intake` artifact、writer、validator、summary helper、CLI 参数和 preflight consumption。Artifact 覆盖 `public_ingress_tls`、`oss_cdn`、`production_db_queue`、`four_g_sim` 四类未来外部证据材料状态，并保持 `production_ready=false`、`overall_status=blocked`、`external_evidence_complete=false`。实现修复了首轮 redaction 误判：固定键名不再包含会触发 forbidden marker 的敏感词，hostile artifact 仍会被阻断。

Task B Robot 完成 metadata-only compatibility fence：

- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`

Robot fence 证明 `external_evidence_intake`、`external_evidence_intake_artifact`、`cloud_external_evidence` 等 metadata 不触发 backend action、不 POST ACK、不推进内存 `last_ack_id`、不持久化 `last_terminal_ack_id`，valid command mixed metadata 只保留 command envelope。

Product closeout 完成本 sprint 留档和 OKR 快照：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_17-18_o5_external-evidence-intake-gate/tech-done.md`
- `sprints/2026.05.13_17-18_o5_external-evidence-intake-gate/side2side_check.md`
- `sprints/2026.05.13_17-18_o5_external-evidence-intake-gate/final.md`

## 验证结果

Task A 返回：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 66 tests in 7.158s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
exit 0

PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --write-external-evidence-intake-artifact /tmp/trashbot_external_evidence_intake.json
"ok": true
"evidence_boundary": "software_proof_docker_external_evidence_intake_gate"
"production_ready": false
"overall_status": "blocked"
"external_evidence_complete": false

PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT=/tmp/trashbot_external_evidence_intake.json python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
"software_proof_ready": true
"production_ready": false
"overall_status": "blocked"
"external_evidence_intake": "pass"

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md
exit 0
```

Task B 返回：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 97 tests in 49.829s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
passed

git diff --check -- docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
passed
```

Product closeout 验收：

```text
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md
exit 0

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_17-18_o5_external-evidence-intake-gate
exit 0
```

## 偏差

- Product planning/closeout worker 两次超时，主节点接管 sprint 文档与 closeout 文档；工程实现、测试、修复和验证仍由 Full-stack / Robot 子 agent 完成。
- 本轮没有真实外部云、OSS/CDN、DB/queue、4G/SIM 材料，因此 Objective 5 不上调。

## 剩余风险

- 本轮证据边界是 `software_proof_docker_external_evidence_intake_gate`，不是真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、真实 OSS/CDN live traffic、真实 production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
