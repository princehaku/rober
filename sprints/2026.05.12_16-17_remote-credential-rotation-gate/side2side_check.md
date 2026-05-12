# Sprint 2026.05.12_16-17 Remote Credential Rotation Gate - Side-by-Side Check

## 状态

- 阶段：side2side_check
- Product acceptance：accepted as Docker/local software proof
- OKR 更新：O6 从约 41% 保守小幅上调到约 43%；O5 保持约 43%；O1-O4 不提升

## 1. 用户价值对照

| 项目 | 本轮前 | 本轮后 |
| --- | --- | --- |
| Credential rotation 可见性 | O6 已有 network recovery drill，但 production credential/STS/account/provisioning/audit-log 缺口主要停留在 preflight blocked reason | 新增 `trashbot.credential_rotation_gate` artifact、preflight check 和 phone-safe 摘要，手机/支持侧能看到凭证轮换软件证明状态与未证明项 |
| 手机/支持侧安全摘要 | 不应泄漏 token、Authorization、OSS secret、AK/SK、路径、串口、ROS topic 或 `/cmd_vel`，但没有 credential rotation 专属摘要 | `/api/status.phone_readiness.credential_rotation` 与 `/api/diagnostics.credential_rotation` 只输出 state、状态枚举、safe summary、retry hint 和 `not_proven` |
| Robot bridge 兼容性 | `remote_bridge` 已有 command/status/ack 保守语义 | 新增 regression 证明 credential/preflight/artifact metadata 不改变 action、ACK、cursor 或 delivery success 语义 |

## 2. 验收证据

Task A - Full-stack / Relay Credential Gate：

- Targeted unittest：`Ran 98 tests in 24.359s`，`OK`
- `py_compile`：passed
- Artifact CLI：`ok=true`、`credential_rotation_status=passed`、`evidence_boundary=software_proof_docker_credential_rotation_gate`
- Preflight CLI：`credential_rotation=pass`、`software_proof_ready=true`、`production_ready=false`、`overall_status=blocked`
- Scoped `git diff --check`：passed
- 首轮失败定位已闭环：安全枚举 `bearer_rotation_status` 被通用脱敏误删；network recovery drill 固定旧时间导致本地 command 过期。

Task B - Robot Compatibility Fence：

- Targeted unittest：`Ran 27 tests in 12.614s`，`OK`
- `remote_bridge.py` `py_compile`：passed
- Scoped `git diff --check`：passed
- 兼容性结论：云端新增 credential/preflight/artifact 字段不触发本地 action、不推进/持久化 cursor，不把 ACK 当成 delivery success。

Product check：

- `tech-done.md` 已整理 Task A、Task B 与 Product acceptance。
- `OKR.md` 已按保守口径更新 O6 到约 43%。
- `docs/product/cloud_4g_infrastructure.md` 已由 Task A 同步，Product 本轮只核对不再扩大文件范围。

## 3. Product 验收结论

本轮验收通过，证据等级为 `software_proof_docker_credential_rotation_gate`。

通过原因：

- Credential rotation gate 已具备 artifact 生成、schema/checksum 校验、preflight 消费和 phone-safe 摘要。
- Preflight 明确保持 `production_ready=false` 与 `overall_status=blocked`。
- Robot bridge 保持 command/status/ack envelope 保守语义。
- 文档与 OKR 没有把本地 software proof 写成真实云或 production-ready。

不通过项或缺口：

- 无真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、CDN origin fetch、生产账号 provisioning、真实 audit log。
- 无 production-ready、生产 DB/queue、正式手机 app/真实手机设备。
- 无 Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 4. 下一步建议

P0：如果继续 O6，应优先推进 production credential provisioning / STS issuance / audit log 的外部实证 gate，而不是继续扩展本地 artifact 字段。

P1：如果真实硬件可接入，应立即切回 O1 HIL evidence packet，补 `command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。

P2：手机侧后续只消费 credential rotation 的 safe summary，不展示 full artifact、checksum、本地路径或凭证细节。
