# Sprint 2026.05.12_14-15 Remote Network Recovery Drill - Tech Plan

## 状态

- 阶段：tech-plan
- 执行方式：team 并行执行
- 主目标：O6 `software_proof_docker_network_recovery_drill`
- 验收策略：测试只做围栏，禁止 broad regression

## 技术方案

本轮把 O6 的网络恢复语义拆成两个互补交付：

1. Relay/phone-safe 侧：生成和消费 network recovery drill artifact。
2. Robot bridge 侧：验证 command/status/ack/cursor 失败时的保守行为。

二者必须共同成立：只有 relay artifact 没有 robot compatibility fence 不算产品闭环；只有 bridge 单测没有 phone-safe artifact 也不能支撑普通用户恢复提示。

## 任务 A：relay network recovery drill 和 phone-safe consumption

- Owner：`full-stack-software-engineer`
- 允许改动范围：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/product/remote_4g_mvp.md`
  - `docs/product/cloud_4g_infrastructure.md`
  - `sprints/2026.05.12_14-15_remote-network-recovery-drill/tech-done.md`

### 实现要求

- 新增 Docker/local 可执行 network recovery drill 入口，优先复用现有 `remote_cloud_relay.py` CLI 风格。
- Drill 覆盖：
  - relay/cloud unreachable 或等价的本地连接失败。
  - ACK post failure 不应被包装成 delivery success。
  - 恢复后 command/status/ack envelope 可重新对账。
  - status stale 能进入 phone-safe blocked/warning。
- 生成 artifact：
  - `schema=trashbot.network_recovery_drill`
  - `schema_version=1`
  - `evidence_boundary=software_proof_docker_network_recovery_drill`
  - `overall_status`
  - `steps`
  - `cursor_invariant`
  - `safe_summary`
  - `retry_hint`
  - `not_proven`
  - `updated_at`
  - `checksum`
- Preflight/diagnostics 消费 artifact：
  - missing：不 green，提示重新运行恢复演练。
  - invalid：不 green，提示恢复演练产物损坏。
  - stale：不 green，提示恢复演练已过期。
  - failed：不 green，提示网络恢复演练失败。
  - passed：只允许进入 software proof ready，不允许说真实云/4G ready。
- Redaction 必须覆盖 bearer token、Authorization、OSS secret、AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 和 `/cmd_vel`。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPATH=src/ros2_trashbot_behavior python3 -m ros2_trashbot_behavior.remote_cloud_relay --network-recovery-drill --state-backend sqlite --state-path /tmp/trashbot_network_recovery.sqlite --write-network-recovery-artifact /tmp/trashbot_network_recovery_drill.json
PYTHONPATH=src/ros2_trashbot_behavior TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT=/tmp/trashbot_network_recovery_drill.json python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md sprints/2026.05.12_14-15_remote-network-recovery-drill/tech-done.md
```

## 任务 B：remote_bridge compatibility fence

- Owner：`robot-software-engineer`
- 允许改动范围：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - `docs/product/remote_4g_mvp.md`
  - `sprints/2026.05.12_14-15_remote-network-recovery-drill/tech-done.md`

### 实现要求

- 覆盖并保留以下保守语义：
  - cloud unreachable：不触发本地 action，不推进 cursor。
  - auth failed：不触发本地 action，不推进 cursor。
  - malformed command/status/ACK response：不触发本地 action，不推进 cursor。
  - ACK post failure：不推进内存 terminal cursor，不写 cursor_state_path。
  - 恢复后：同一 command 可重试；terminal ACK 成功后才允许持久化 cursor。
- 如果现有实现已满足，允许只补 targeted compatibility fence 和文档，不做产品代码改动。
- 不新增硬件、Nav2、WAVE ROVER、串口或 HIL 相关逻辑。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/product/remote_4g_mvp.md sprints/2026.05.12_14-15_remote-network-recovery-drill/tech-done.md
```

## 任务 C：集成验收和 sprint 收口

- Owner：`product-okr-owner`
- 允许改动范围：
  - `OKR.md`
  - `sprints/2026.05.12_14-15_remote-network-recovery-drill/tech-done.md`
  - `sprints/2026.05.12_14-15_remote-network-recovery-drill/side2side_check.md`
  - `sprints/2026.05.12_14-15_remote-network-recovery-drill/final.md`

### 验收口径

- 只接受 `software_proof_docker_network_recovery_drill`。
- O6 可按证据保守小幅上调；O5 只记录 phone-safe 支撑，不作为主目标上调，除非有真实手机/浏览器新增证据。
- O1/O2/O3/O4 不上调。
- 必须明确未完成：
  - 真实云部署。
  - HTTPS/TLS。
  - 公网入口。
  - 真实 4G/SIM。
  - 生产鉴权/rotate。
  - STS/受限 AK。
  - 真实 OSS upload。
  - CDN origin fetch。
  - 生产 DB/queue。
  - 多实例一致性。
  - 正式手机 app/真实手机设备验收。
  - Nav2/fixed-route、WAVE ROVER、HIL、真实送达。

### Product 验收命令

```bash
git diff --check -- sprints/2026.05.12_14-15_remote-network-recovery-drill/tech-done.md sprints/2026.05.12_14-15_remote-network-recovery-drill/side2side_check.md sprints/2026.05.12_14-15_remote-network-recovery-drill/final.md OKR.md
```

## 并行执行规则

任务 A 和任务 B 文件范围基本互不重叠，但共享 `docs/product/remote_4g_mvp.md` 和 `tech-done.md`。执行时应优先由 `full-stack-software-engineer` 写 docs 中 relay/artifact 段，由 `robot-software-engineer` 写 bridge/cursor 段；如果出现冲突，由 `robot-software-engineer` 负责 compatibility fence 语义事实，`full-stack-software-engineer` 负责 phone-safe consumption 表述。

Codex 运行时应在 implementation 阶段并行派发：

- `spawn_agent(agent_type=worker)` for `full-stack-software-engineer`
- `spawn_agent(agent_type=worker)` for `robot-software-engineer`

本阶段用户明确要求只做产品计划和 sprint 开局，因此不进入 implementation。

## 当前计划文档验收命令

```bash
git diff --check -- sprints/2026.05.12_14-15_remote-network-recovery-drill/pre_start.md sprints/2026.05.12_14-15_remote-network-recovery-drill/prd.md sprints/2026.05.12_14-15_remote-network-recovery-drill/tech-plan.md
```

## 风险边界

- 本轮不能把 Docker/local 网络恢复 drill 宣称为真实 4G/SIM 或生产云恢复能力。
- 本轮不能把 ACK 解释成 delivery success。
- 本轮不能暴露 `/cmd_vel`、raw ROS topic、串口、WAVE ROVER 参数或任何凭证。
- 本轮不新增广泛测试；只跑目标 unittest、py_compile、CLI/Docker smoke 和 scoped diff check。
- 如果无 artifact、无 compatibility fence 或无 phone-safe consumption，则 O6 不应上调。
