# Sprint 2026.05.13_17-18 O5 External Evidence Intake Gate - Tech Plan

## 目标

新增 O5 external evidence intake gate，让系统能安全接收未来真实云、OSS/CDN、DB/queue、4G/SIM 外部证据材料，并输出脱敏 artifact、preflight check 和 phone-safe readiness handoff。当前 Docker-only 主机若没有真实外部材料，本轮只能形成 blocked software proof，不上调 OKR。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 67%；Objective 4 约 70%，Objective 1/2/3 分别约 75/77/77。
2. 本 sprint 针对当前最低 Objective 5。
3. 证据理由：`2026.05.13_12-13_cloud-db-queue-external-probe-gate` 已完成 DB/queue external probe bundle；`2026.05.13_14-15_oss-cdn-live-probe-gate` 已完成 OSS/CDN live probe artifact；`2026.05.13_16-17_mobile-web-browser-proof-gate` 明确下一轮 O5 不应继续堆本地 metadata，而要引入真实外部证据或形成可交接 blocked evidence。当前本机只有 Docker，因此本轮抓手是 external evidence intake gate：让未来真实材料有安全入口，并把当前缺失状态明确交接。

## 证据边界

- 允许声明：`software_proof_docker_external_evidence_intake_gate`，以及“外部证据材料 intake schema / redaction / preflight consumption 可验证”。
- 未拿到真实外部材料时必须声明：`production_ready=false`、`overall_status=blocked`、`external_evidence_complete=false`。
- 禁止声明：真实云、真实 HTTPS/TLS 公网入口、真实 4G/SIM、真实 OSS/CDN live traffic、真实 production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实投放或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed 或 true task completion。

## Task A - Full-Stack Software Engineer

Owner: `full-stack-software-engineer`

任务：

- 在 relay/preflight 体系新增 `trashbot.external_evidence_intake` artifact。
- Artifact 覆盖四类外部材料状态：`public_ingress_tls`、`oss_cdn`、`production_db_queue`、`four_g_sim`。
- 只保存枚举状态、脱敏摘要、材料时间、证据边界、`not_proven`、`safe_summary`、`retry_hint` 和 checksum；不得保存 URL、credential-bearing endpoint、token、Authorization、OSS AK/SK、DB/queue URL、响应体、本地路径或 traceback。
- 新增 CLI writer 和 preflight consumption，环境变量建议为 `TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT`，CLI 参数建议为 `--external-evidence-intake-artifact` / `--write-external-evidence-intake-artifact`。
- 同步 `cloud-relay/README.md`、`docs/product/remote_4g_mvp.md`、`docs/product/cloud_4g_infrastructure.md`。

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --write-external-evidence-intake-artifact /tmp/trashbot_external_evidence_intake.json
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT=/tmp/trashbot_external_evidence_intake.json python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md
```

验收口径：

- Valid local artifact 只能证明 schema、checksum、redaction 和 preflight consumption。
- 无真实外部材料时，summary 必须保持 blocked，不得把 intake gate 写成 live cloud proof。
- Forbidden marker 测试必须覆盖 token、Authorization、AK/SK、DB/queue URL、credential-bearing URL、traceback、ROS topic、`/cmd_vel`。

## Task B - Robot Software Engineer

Owner: `robot-software-engineer`

任务：

- 增加 metadata-only compatibility fence，证明 `external_evidence_intake`、`external_evidence_intake_artifact`、`cloud_external_evidence` 等 metadata 不会被 `remote_bridge` 当作 command/status/ACK envelope。
- 更新 `docs/interfaces/ros_contracts.md`，明确该 metadata 只是 cloud readiness proof，不触发 robot action、不 POST ACK、不推进 `last_ack_id` 或 `last_terminal_ack_id`。

文件范围：

- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

验收口径：

- Metadata-only response 不得触发 backend action。
- 不得 POST ACK。
- 不得推进内存 cursor。
- 不得持久化 `last_terminal_ack_id`。

## Task C - Product OKR Owner

Owner: `product-okr-owner`

任务：

- 等待 Task A/B 返回后更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 根据实际证据更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 如果本轮没有真实外部材料，只记录 O5 blocked software proof，不上调 Objective 5。

文件范围：

- `sprints/2026.05.13_17-18_o5_external-evidence-intake-gate/tech-done.md`
- `sprints/2026.05.13_17-18_o5_external-evidence-intake-gate/side2side_check.md`
- `sprints/2026.05.13_17-18_o5_external-evidence-intake-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

验收命令：

```bash
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_17-18_o5_external-evidence-intake-gate
```

验收口径：

- `tech-done.md` 记录 A/B 实际改动、验证结果、偏差和剩余风险。
- `side2side_check.md` 对照用户要求：O5 最低优先级、具体证据、team 执行、测试围栏、Docker-only 边界、功能向前。
- `final.md` 必须写清是否有真实外部材料；没有则不调整 OKR 完成度。

## 并行执行要求

- Task A 与 Task B 可并行启动，文件范围不重叠。
- Task C 必须等待 Task A/B 返回后再收口。
- 主节点只做派发、等待、验收、留档整合、commit/push；产品代码、测试代码和工程验证由对应子 agent 完成。

## 风险和回滚边界

- 不回滚他人改动；若文件已有并行改动，子 agent 必须适配并在返回中说明。
- 不扩大到硬件、Nav2、真实云凭证或 production secret。
- 若 external evidence intake artifact 泄漏敏感字段，必须修复后才能收口。
- 若 robot compatibility fence 失败，Task C 不得更新 OKR 完成度。
