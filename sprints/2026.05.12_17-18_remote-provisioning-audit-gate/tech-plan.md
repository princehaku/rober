# Sprint 2026.05.12_17-18 Remote Provisioning Audit Gate - Tech Plan

## 0. 执行边界

- 本文件是下一轮实现计划，不在计划阶段修改产品代码。
- 当前主机是 Docker/local，无真实硬件、无真实 4G/SIM、无真实云账号实证。
- 本轮目标 evidence boundary：`software_proof_docker_provisioning_audit_gate`。
- 禁止声明：真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、真实 audit log、production-ready、WAVE ROVER、HIL、Nav2/fixed-route 或真实送达。

## 1. 任务分工

### Task A - Full-stack owner：Relay / Preflight / Phone-safe Provisioning Audit Gate

Owner：`full-stack-software-engineer`

允许改动文件范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-done.md`

实现目标：

- 新增 robot provisioning、STS issuance、audit log 三类 artifact schema/helper/CLI 入口。
- 新增 env/CLI driven preflight consumption。
- 新增 `/api/status.phone_readiness.provisioning_audit` 和 `/api/diagnostics.provisioning_audit` 或等价 phone-safe 摘要。
- 所有输出必须保留 `not_proven`，不得泄露 bearer token、Authorization、OSS secret、AK/SK、root password、credential URL、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic、`/cmd_vel` 或 traceback。
- `production_ready=false` 和 `overall_status=blocked` 必须保持，除非未来真实云证据补齐；本轮不得改成 ready。

建议 CLI/env：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-provisioning-audit-artifact /tmp/trashbot_provisioning_audit_gate.json \
  --provisioning-audit-robot-id robot-local-proof
```

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT=/tmp/trashbot_provisioning_audit_gate.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
```

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-provisioning-audit-artifact /tmp/trashbot_provisioning_audit_gate.json \
  --provisioning-audit-robot-id robot-local-proof
```

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT=/tmp/trashbot_provisioning_audit_gate.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight || true
```

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-done.md
```

### Task B - Robot owner：Remote Bridge Compatibility Fence

Owner：`robot-software-engineer`

允许改动文件范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-done.md`

实现目标：

- 为 command/status/ack 响应新增 provisioning/STS/audit metadata fixtures。
- 证明 robot bridge 忽略未知 production gate metadata。
- 证明 GET outage、invalid metadata、preflight blocked 不触发本地 action、不 ACK、不推进或持久化 cursor。
- 证明 ACK 仍只表示 command envelope processed，不等于 delivery success。
- 如果 `remote_bridge.py` 已满足语义，优先只新增测试，不做无意义改动。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-done.md
```

### Task C - Product owner：Acceptance / OKR Closure

Owner：`product-okr-owner`

允许改动文件范围：

- `OKR.md`
- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-done.md`
- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/side2side_check.md`
- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/final.md`

验收目标：

- 核对 Task A/Task B 实际命令输出和失败定位。
- 确认 docs/product 已同步，且没有把本地 gate 写成真实云或生产 ready。
- 根据证据保守更新 O6 进度；若三条 gate 和 compatibility fence 都通过，建议 O6 约 43% -> 约 45%。
- O5 只记录支撑素材，不因本轮自动提升。
- 明确未完成事项和下一轮建议。

验收命令：

```bash
git diff --check -- \
  OKR.md \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-done.md \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/side2side_check.md \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/final.md
```

## 2. 并行启动规则

进入实现阶段后，Task A 和 Task B 文件范围互不重叠，必须并行启动：

- `full-stack-software-engineer` 执行 Task A。
- `robot-software-engineer` 执行 Task B。

Task C 只能在 Task A/Task B 返回后执行验收和 OKR 收口。

## 3. 接口影响

Remote relay / operator API：

- 允许新增 provisioning/audit gate 相关 phone-safe summary 字段。
- 不允许删除或破坏既有 `phone_readiness.credential_rotation`、`phone_readiness.network_recovery`、`phone_readiness.oss_cdn_manifest`、`command_safety` 字段。
- 不允许向 phone-safe API 返回完整 artifact、checksum、本地路径、token、secret 或 traceback。

Remote bridge：

- 不新增机器人执行命令类型。
- 不改变 command/status/ack envelope 的保守语义。
- 不把 preflight 或 audit metadata 当成本地 action。

Docs：

- `docs/product/cloud_4g_infrastructure.md` 必须新增本轮 boundary、CLI/env、non-goals 和 redaction 说明。
- `docs/product/remote_4g_mvp.md` 必须新增本轮 gate 的手机/云中转产品口径。

## 4. 风险边界

- 本轮不是 production credential provisioning。
- 本轮不是真实 STS issuance。
- 本轮不是真实 audit log。
- 本轮不是真实 OSS upload、CDN origin fetch、生命周期策略或 production account。
- 本轮不是真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、生产 DB/queue、多实例一致性或生产备份策略。
- 本轮不是正式手机 app、真实手机设备验收、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 5. 计划阶段验证

本阶段只验证三个计划文档格式：

```bash
git diff --check -- \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/pre_start.md \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/prd.md \
  sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-plan.md
```
