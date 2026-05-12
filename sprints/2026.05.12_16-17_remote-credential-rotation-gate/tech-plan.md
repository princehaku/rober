# Sprint 2026.05.12_16-17 Remote Credential Rotation Gate - Tech Plan

## 状态

- 阶段：tech-plan
- 主目标：O6 `software_proof_docker_credential_rotation_gate`
- 计划状态：ready for implementation
- 验证策略：功能往前走，测试只做围栏；不跑 broad regression

## 1. 技术方案概述

在现有 independent `remote_cloud_relay.py`、production preflight、operator/API phone readiness/diagnostics 和 remote bridge compatibility fence 之上，新增一个 Docker/local credential rotation gate。它用 artifact 表达“生产凭证 rotate/STS 边界是否具备本地 proof”，由 preflight 消费并由 phone-safe diagnostics 展示摘要。

本轮仍属于 Docker/local software proof，不引入真实云账号、真实 OSS 上传、真实 STS 签发、CDN 回源或 4G/SIM。

## 2. 文件范围和 owner

### Task A - Full-stack / Relay Credential Gate

Owner：`full-stack-software-engineer`

允许改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/cloud_4g_infrastructure.md`
- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-done.md`

需要完成：

- 新增 credential rotation artifact schema，建议字段：
  - `schema=trashbot.credential_rotation_gate`
  - `schema_version=1`
  - `evidence_boundary=software_proof_docker_credential_rotation_gate`
  - `robot_id`
  - `generated_at`
  - `bearer_rotation_status`
  - `oss_credential_mode`
  - `sts_boundary_status`
  - `account_tier_status`
  - `robot_provisioning_status`
  - `audit_log_status`
  - `not_proven`
  - `safe_summary`
  - `retry_hint`
  - `checksum`
- 新增 CLI 或 env-driven artifact 入口，例如 `--write-credential-rotation-artifact` 和 `TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT`。
- `--preflight` / `/preflightz` 消费 artifact，输出 `credential_rotation` check；artifact valid 时该 check 可 pass，但 production 缺口仍保持 `production_ready=false`。
- `/api/status.phone_readiness` 或 `/api/diagnostics` 增加 credential rotation phone-safe 摘要。
- hostile redaction fence 覆盖 token、Authorization、OSS secret、AK/SK、root password、state path、serial、baudrate、WAVE ROVER、ROS topic、`/cmd_vel`。
- 同步 `docs/product/cloud_4g_infrastructure.md`，明确本轮 boundary 和 non-goals。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py

PYTHONPATH=src/ros2_trashbot_behavior python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-credential-rotation-artifact /tmp/trashbot_credential_rotation_gate.json \
  --credential-rotation-robot-id robot-local-proof

PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT=/tmp/trashbot_credential_rotation_gate.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight

git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  docs/product/cloud_4g_infrastructure.md \
  sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-done.md
```

### Task B - Robot Compatibility Fence

Owner：`robot-software-engineer`

允许改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `docs/product/cloud_4g_infrastructure.md`
- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-done.md`

需要完成：

- 确认 credential rotation gate 不会改变 `remote_bridge` 的保守语义。
- auth failed、cloud unreachable、malformed response、ACK post failure 时不得推进 cursor，不得持久化 terminal ACK，不得触发本地 action。
- artifact/preflight 的新字段如果进入 status 或 diagnostics，remote bridge 仍只处理 command/status/ack envelope，不把 ACK 写成 delivery success。
- 如果现有代码已满足，只补最小 compatibility fence 和 docs/sprint 证据，不做无关重构。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py

git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  docs/product/cloud_4g_infrastructure.md \
  sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-done.md
```

### Task C - Product Acceptance and OKR Closure

Owner：`product-okr-owner`

允许改动：

- `OKR.md`
- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-done.md`
- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/side2side_check.md`
- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/final.md`

需要完成：

- 汇总 Task A/B 的实际输出、验证命令和失败定位。
- 判断 O6 是否只可保守小幅提升；不得因为 artifact/preflight pass 宣称 production-ready。
- 明确本轮仍没有真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、CDN origin fetch、生产 DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- 更新 `OKR.md` 当前快照和剩余缺口。

验收命令：

```bash
git diff --check -- \
  OKR.md \
  sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-done.md \
  sprints/2026.05.12_16-17_remote-credential-rotation-gate/side2side_check.md \
  sprints/2026.05.12_16-17_remote-credential-rotation-gate/final.md
```

## 3. 并行和接口边界

- Task A 与 Task B 文件范围基本分离，可并行启动。
- `docs/product/cloud_4g_infrastructure.md` 和 `tech-done.md` 是共享文件；如果并行实现时发生冲突，由 Task A 先写功能边界，Task B 追加 compatibility 证据，Product 最后收口整理。
- Task A 不得改 remote bridge 的 action 触发或 cursor 语义。
- Task B 不得实现 relay artifact 或 phone UI 摘要。
- Product 不改产品代码或测试代码。

## 4. 验收口径

本轮通过条件：

- 能生成 credential rotation artifact，并通过 schema/version/checksum/phone-safe 校验。
- Preflight 可消费 artifact，并输出 credential rotation check。
- Phone/API diagnostics 有 credential rotation safe summary 或等效摘要。
- hostile redaction 不泄漏 token、Authorization、OSS secret、AK/SK、root password、state path、serial、baudrate、WAVE ROVER、ROS topic、`/cmd_vel`。
- Remote bridge compatibility fence 保持 auth/ACK/cursor 保守语义。
- `tech-done.md`、`side2side_check.md`、`final.md` 和 `OKR.md` 在实现完成后同步更新。

本轮失败条件：

- Artifact 或 diagnostics 泄漏凭证、内部路径、ROS topic 或硬件字段。
- Preflight 在真实云、HTTPS/TLS、公网入口、STS、OSS upload、CDN origin fetch 未证明时输出 production-ready。
- ACK 文案被写成 delivery success。
- 只新增测试而没有 artifact/preflight/phone-safe consumption 功能前进。

## 5. 风险和非目标

- 非目标：真实云部署、真实 4G/SIM outbound polling、真实 OSS upload、真实 STS issuance、CDN origin fetch、生产账号 provisioning、真实 audit log、production-ready、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- 风险：credential rotation gate 的名字容易被误读为生产 rotate 已完成；所有输出必须同时携带 `software_proof_docker_credential_rotation_gate` 和 `not_proven`。
- 风险：测试范围膨胀；本轮只跑 Task A/B/C 中列出的 targeted unittest、py_compile、CLI/preflight smoke 和 scoped `git diff --check`。

## 6. 本启动文档验证

Product Owner 创建本启动阶段三份文档后，只运行：

```bash
git diff --check -- \
  sprints/2026.05.12_16-17_remote-credential-rotation-gate/pre_start.md \
  sprints/2026.05.12_16-17_remote-credential-rotation-gate/prd.md \
  sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-plan.md
```
