# Sprint 2026.05.12_17-18 Remote Provisioning Audit Gate - Tech Done

## Task A - Full-stack owner: Relay / Preflight / Phone-safe Provisioning Audit Gate

状态：完成。

用户旅程变化和触点收益：

- 手机/API 现在可以在 `/api/status.phone_readiness.provisioning_audit` 看到 production provisioning / STS / audit 三类上线前 gate 的 phone-safe 摘要。
- 支持入口现在可以在 `/api/diagnostics.provisioning_audit` 看到同一摘要，用于复现“为什么还不能 production ready”，但不暴露 artifact 路径、checksum、机器人标识、凭证、串口、ROS topic 或 traceback。
- `remote_cloud_relay --preflight` 可以通过 `TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT` 或 `--provisioning-audit-artifact` 消费该 artifact；有效 artifact 只把 `software_proof_ready` 置为 true，`production_ready=false` 与 `overall_status=blocked` 保持不变。

实际改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `trashbot.provisioning_audit_gate` artifact schema/helper/validator/phone summary/CLI。
  - 新增 `--write-provisioning-audit-artifact`、`--provisioning-audit-robot-id`、`--provisioning-audit-artifact` 和 `TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT` preflight consumption。
  - 新增 `provisioning_audit` preflight check，证据边界为 `software_proof_docker_provisioning_audit_gate`；输出持续保留 `not_proven`、`production_ready=false`、`overall_status=blocked`。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - `/api/status.phone_readiness` 新增 `provisioning_audit` 摘要字段。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `/api/diagnostics` 新增 `provisioning_audit` 摘要字段。
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 覆盖 artifact 生成、invalid/stale/hostile fail-closed、preflight consumption 和 missing/invalid artifact。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - 覆盖 `/api/status.phone_readiness.provisioning_audit` phone-safe ready 摘要。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 覆盖 `/api/diagnostics.provisioning_audit` phone-safe ready 摘要。
- `docs/product/cloud_4g_infrastructure.md`
  - 更新 provisioning audit gate、env、CLI、preflight 和证据边界说明。
- `docs/product/remote_4g_mvp.md`
  - 更新用户触点的 provisioning audit 摘要、CLI 和不可越界项。

接口影响：

- 新增 artifact schema：`trashbot.provisioning_audit_gate`。
- 新增 evidence boundary：`software_proof_docker_provisioning_audit_gate` 与 `software_proof_docker_provisioning_audit_phone_consumption`。
- 新增 CLI/env：
  - `--write-provisioning-audit-artifact`
  - `--provisioning-audit-robot-id`
  - `--provisioning-audit-artifact`
  - `TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT`
- 新增 API 摘要字段：
  - `/api/status.phone_readiness.provisioning_audit`
  - `/api/diagnostics.provisioning_audit`

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
.......................................................................................................
----------------------------------------------------------------------
Ran 103 tests in 24.406s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
通过，无输出。
```

```text
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-provisioning-audit-artifact /tmp/trashbot_provisioning_audit_gate.json \
  --provisioning-audit-robot-id robot-local-proof
输出包含：
ok=true
evidence_boundary=software_proof_docker_provisioning_audit_gate
provisioning_audit_status=blocked
production_ready=false
overall_status=blocked
not_proven 包含 real_sts_issuance、real_audit_log_sink、real_cloud、real_4g_sim、nav2_or_fixed_route_delivery、wave_rover_or_hil。
```

```text
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT=/tmp/trashbot_provisioning_audit_gate.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight || true
输出包含：
software_proof_ready=true
production_ready=false
overall_status=blocked
evidence_boundary=software_proof_docker_provisioning_audit_gate
checks.provisioning_audit.status=pass
checks.provisioning_audit.details.production_ready=false
not_proven 包含 production_robot_provisioning、real_sts_issuance、real_audit_log_sink、real_cloud、real_4g_sim、nav2_or_fixed_route_delivery、wave_rover_or_hil。
```

偏差与风险：

- 本轮证据边界是 `software_proof_docker_provisioning_audit_gate`，不是真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、真实 audit log、production-ready、WAVE ROVER、HIL、Nav2/fixed-route 或真实送达。
- Preflight 在本地默认环境仍因凭证、公网/TLS、OSS/CDN、state store 等生产项 blocked；这是预期阻断，不是生产可用证明。
- Robot-side metadata compatibility 由 Task B 覆盖；Task A 没有改动 `remote_bridge.py`。

## Task B - Robot owner: Remote Bridge Compatibility Fence

状态：完成。

实际改动：

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 新增 provisioning / STS / audit metadata 兼容性测试，覆盖 command/status/ack 响应带 production gate metadata 时 robot bridge 只处理既有 command envelope。
  - 新增 metadata-only + preflight blocked 测试，确认没有 command envelope 时不触发本地 action、不 ACK、不推进 `last_ack_id`、不持久化 cursor。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - 未改动。现有实现已保持 unknown metadata 保守兼容，Task B 只补测试围栏。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
.............................
----------------------------------------------------------------------
Ran 29 tests in 14.201s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
通过，无输出。
```

```text
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-done.md
通过，无输出。
```

偏差与风险：

- 本轮只证明 robot-side Python compatibility fence，不证明真实云、真实 4G/SIM、真实 STS issuance、真实 audit log、production-ready、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- `remote_bridge.py` 没有新增本地 action 类型；ACK 仍只表示 command envelope 已处理或提交，不等于 delivery success。

## Task C - Product owner: Acceptance / OKR Closure

状态：完成。

验收判断：

- Task A 通过。`trashbot.provisioning_audit_gate` 已覆盖 robot provisioning、STS issuance boundary、audit log contract 三类上线前阻断项，并接入 artifact CLI、preflight consumption、`/api/status.phone_readiness.provisioning_audit` 和 `/api/diagnostics.provisioning_audit`。
- Task B 通过。新增 provisioning/STS/audit metadata 不改变 remote bridge 的 command/status/ack envelope，不触发额外本地 action，不 ACK，不推进或持久化 cursor；ACK 仍不等于 delivery success。
- `docs/product/cloud_4g_infrastructure.md` 与 `docs/product/remote_4g_mvp.md` 已同步记录 CLI/env、preflight、phone-safe 摘要和 non-goals。

OKR 收口：

- O6 从约 43% 保守小幅上调到约 45%，证据边界为 `software_proof_docker_provisioning_audit_gate`。
- O5 保持约 43%，本轮只新增 phone-safe 摘要素材，不构成正式手机 app 或真实手机设备验收。
- O1/O2/O3/O4 不提升。

证据边界：

- 本轮是 Docker/local software proof，只证明 provisioning/STS/audit gate 的 schema、checksum、preflight consumption、phone-safe 摘要和 robot bridge compatibility。
- 本轮不是真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、真实 audit log、production-ready、正式手机 app/真实手机设备、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

Task C 验证：

```text
git diff --check -- \
  OKR.md \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-done.md \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/side2side_check.md \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/final.md
通过，无输出。
```

剩余风险：

- 当前仍缺真实 production account provisioning、真实 STS issuance、真实 audit sink、真实 OSS upload、真实云入口、真实 4G/SIM 和生产级持久化/运维证据。
- 如果仍是 Docker-only 主机，下一轮 O6 应推进外部云最小 sandbox、production ingress/TLS、真实 STS 或真实 OSS 实证之一；如果接入真实串口硬件，则切回 O1 HIL evidence packet。
