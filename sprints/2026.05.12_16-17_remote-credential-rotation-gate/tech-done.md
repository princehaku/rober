# Sprint 2026.05.12_16-17 Remote Credential Rotation Gate - Tech Done

## Task A - Full-stack / Relay Credential Gate

状态：implemented, verified.

实际改动：

- `remote_cloud_relay.py` 新增 `trashbot.credential_rotation_gate` artifact schema、生成/校验 helper、`--write-credential-rotation-artifact`、`--credential-rotation-robot-id` 和 `TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT` preflight 消费入口。
- `--preflight` / `/preflightz` 新增 `credential_rotation` check；artifact valid 时该 check 为 `pass`，整体仍保持 `production_ready=false`，并继续在 `not_proven` 中保留 production credential rotation、STS issuance、真实云、真实 4G/SIM、真实 OSS/CDN、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达缺口。
- `operator_gateway_http.py` 与 `operator_gateway_diagnostics.py` 新增 phone-safe credential rotation 摘要消费，只返回 state、状态枚举、safe summary、retry hint 和 `not_proven`，不返回完整 artifact、checksum、路径、token、Authorization、OSS secret、AK/SK、root password、串口、baudrate、WAVE ROVER、ROS topic 或 `/cmd_vel`。
- Targeted tests 覆盖 artifact 生成/校验、preflight pass/missing/invalid、hostile redaction、`/api/status.phone_readiness.credential_rotation` 和 `/api/diagnostics.credential_rotation`。
- `docs/product/cloud_4g_infrastructure.md` 同步记录本轮 `software_proof_docker_credential_rotation_gate` boundary、CLI/env 入口和 non-goals。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest ...
Ran 98 tests in 24.359s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile ...
passed
```

```text
python3 -m ros2_trashbot_behavior.remote_cloud_relay --write-credential-rotation-artifact ...
ok=true
credential_rotation_status=passed
evidence_boundary=software_proof_docker_credential_rotation_gate
```

```text
TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT=/tmp/trashbot_credential_rotation_gate.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
credential_rotation=pass
software_proof_ready=true
production_ready=false
overall_status=blocked
evidence_boundary=software_proof_docker_credential_rotation_gate
```

```text
git diff --check -- <Task A files>
passed
```

偏差和剩余风险：

- 本轮只完成 Docker/local software proof，不声明真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、CDN origin fetch、production-ready、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- Task B `remote_bridge.py` / `test_remote_bridge.py` 属于另一个 worker，本 Task A 未修改。

## Task B - Robot Compatibility Fence

状态：implemented, verified.

实际改动：

- `test_remote_bridge.py` 新增 mock cloud credential/preflight metadata fixtures，覆盖 future credential rotation、preflight 和 diagnostics 字段进入云响应时的兼容性。
- 新增 GET outage regression，证明 command polling 失败时不触发本地 action、不发送 ACK、不推进 cursor、不持久化 cursor。
- 新增 envelope regression，证明 `remote_bridge` 忽略 command/status/ack 响应中的 credential/preflight/artifact 附加字段，并且不把 ACK 解释成 delivery success。
- `remote_bridge.py` 无需代码改动；现有保守语义已满足本轮接口边界。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 27 tests in 12.614s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
exit 0
```

```text
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
exit 0
```

偏差和剩余风险：

- 本轮 compatibility fence 是 Docker/local software proof，不覆盖真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- Task B 未修改 relay artifact/preflight/phone-safe 摘要实现，避免跨 owner 扩大范围。

## Task C - Product Acceptance and OKR Closure

状态：accepted, closed as software proof.

用户价值和产品北极星：

- 用户价值：手机/支持侧现在能看到“凭证轮换 gate 是否具备本地软件证明”的脱敏摘要，知道上线前卡在 production credential/STS/account/provisioning/audit-log 哪些边界，而不是只看到 remote cloud blocked。
- 产品北极星：继续推进“普通手机用户通过 4G 云中转控制小车”的 O6 主线，但严格保持证据边界，不能把本地 artifact/preflight pass 当成真实云或生产可用。

OKR 映射和 KR 更新：

- Objective 6：命中 KR1 的 command/status/ack 兼容边界、KR3/KR4/KR5 的 OSS/CDN 与凭证管理边界、KR6 的 graceful degradation/diagnostics 可解释性。
- 本轮只支持 O6 从约 41% 保守小幅上调到约 43%。
- Objective 5 保持约 43%；O1/O2/O3/O4 不提升。

本轮核心抓手：

- Task A 把 credential rotation 从文档风险推进到 artifact/preflight/phone-safe 摘要的可执行 gate。
- Task B 证明 robot bridge 对新增 artifact/preflight metadata 保持保守，不因云端扩展字段改变 action、ACK 或 cursor 语义。

Product acceptance 判断：

- 接受 Task A：artifact 生成、preflight 消费、phone-safe 摘要、hostile redaction 和 `docs/product/cloud_4g_infrastructure.md` 同步已完成；首轮失败已定位并修复。
- 接受 Task B：remote bridge compatibility fence 通过；`remote_bridge.py` 无需代码改动是合理结果。
- 接受本轮 O6 小幅进展：证据链达到 `software_proof_docker_credential_rotation_gate`，但生产缺口仍明确 blocked。

Product 验收命令：

```text
git diff --check -- OKR.md sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-done.md sprints/2026.05.12_16-17_remote-credential-rotation-gate/side2side_check.md sprints/2026.05.12_16-17_remote-credential-rotation-gate/final.md
passed
```

未完成事项和风险：

- 没有真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、CDN origin fetch、生产账号 provisioning、真实 audit log、production-ready、生产 DB/queue、正式手机 app/真实手机设备、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- 下一轮 O6 若继续推进，应优先把 production credential provisioning / STS / audit log 从 blocked reason 推到外部实证；若硬件可用，应回到 O1 HIL。
