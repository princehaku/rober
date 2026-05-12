# Sprint 2026.05.12_16-17 Remote Credential Rotation Gate - Final

## 状态

- Sprint 状态：closed
- 关闭口径：O6 Docker/local software proof accepted
- Evidence boundary：`software_proof_docker_credential_rotation_gate`
- OKR 结果：O6 约 41% -> 约 43%；O5 保持约 43%；O1-O4 不提升

## 1. 本轮为什么做 O6

当前主机没有真实硬件，无法形成 O1 HIL 或真实送达证据。上一轮 `2026.05.12_15-16_phone-browser-acceptance-gate` 已把 O5 推进到约 43%，而 O6 停在约 41%。按“优先推进 OKR 完成度低的部分”和“功能往前走”的规则，本轮选择 O6 credential rotation gate，继续补远程云中转产品化的生产前置证明。

## 2. 实际交付

Task A - Full-stack / Relay Credential Gate：

- 新增 `trashbot.credential_rotation_gate` artifact schema、生成/校验 helper、CLI 写入入口和 env-driven preflight 消费入口。
- `/preflightz` / `--preflight` 新增 `credential_rotation` check；有效 artifact 可使该 check `pass`，但整体仍保持 `production_ready=false` 和 `overall_status=blocked`。
- `/api/status.phone_readiness.credential_rotation` 与 `/api/diagnostics.credential_rotation` 新增 phone-safe 摘要。
- `docs/product/cloud_4g_infrastructure.md` 已同步 boundary、CLI/env 入口和 non-goals。

Task B - Robot Compatibility Fence：

- 新增 `test_remote_bridge.py` compatibility fence，覆盖 credential/preflight metadata、GET outage、cursor/ACK 保守语义。
- `remote_bridge.py` 无需修改，现有 conservative envelope handling 已满足要求。

Task C - Product Acceptance：

- 整理 `tech-done.md`，创建 `side2side_check.md` 与 `final.md`。
- 更新 `OKR.md` 当前快照，O6 保守上调到约 43%。

## 3. 验证结果

Task A：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest ...
Ran 98 tests in 24.359s
OK
```

```text
artifact CLI:
ok=true
credential_rotation_status=passed
evidence_boundary=software_proof_docker_credential_rotation_gate
```

```text
preflight CLI:
credential_rotation=pass
software_proof_ready=true
production_ready=false
overall_status=blocked
```

Task B：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 27 tests in 12.614s
OK
```

Product acceptance：

```text
git diff --check -- OKR.md sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-done.md sprints/2026.05.12_16-17_remote-credential-rotation-gate/side2side_check.md sprints/2026.05.12_16-17_remote-credential-rotation-gate/final.md
passed
```

## 4. 失败定位

Task A 第一轮发现并修复两个问题：

- 安全枚举 `bearer_rotation_status` 被通用脱敏误删，导致 phone-safe 输出不可用。
- Network recovery drill 固定旧时间导致本地 command 过期。

Product acceptance 未发现新的验证失败。

## 5. 剩余风险

本轮仍没有：

- 真实云、HTTPS/TLS、公网入口、真实 4G/SIM。
- 真实 OSS upload、真实 STS issuance、CDN origin fetch。
- 生产账号 provisioning、真实 audit log、production-ready、生产 DB/queue。
- 正式手机 app、真实手机设备、普通用户远程验收。
- Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

Credential rotation gate 的 `pass` 只代表 Docker/local artifact 与 preflight/phone-safe contract 成立，不代表生产凭证轮换已经完成。

## 6. 下一轮建议

如果仍处于 Docker-only 环境，下一轮 O6 应推进 production credential provisioning / STS issuance / audit log 的外部 proof，而不是继续增加本地 mock 字段。

如果出现真实串口硬件，优先切回 O1，执行 WAVE ROVER `hil_pass` evidence packet，并保持 `software_proof` 与真实 `hil_pass` 分离。
