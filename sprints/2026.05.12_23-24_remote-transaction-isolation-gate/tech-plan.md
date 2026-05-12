# Sprint 2026.05.12_23-24 Remote Transaction Isolation Gate - Tech Plan

## 状态

- 阶段：tech-plan
- Product Owner：`product-okr-owner`
- 主线 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- 目标证据：`software_proof_docker_transaction_isolation_gate`
- 执行模式：team execution；Task A 与 Task B 文件范围不重叠，可并行启动。

## 技术目标

新增 Docker/local transaction isolation gate。它必须生成和消费 `trashbot.transaction_isolation_drill` artifact/preflight/phone-safe summary，验证同一 robot 的并发 command/status/ack 写入不会让 ACK cursor 越过未完成命令，也不会把 ACK 升级为 delivery success。

本轮保持 `production_ready=false`，明确不等于真实生产 DB/queue、多实例一致性、真实生产 transaction isolation、真实云、真实 4G、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 接口和证据边界

新增 artifact contract：

- `schema=trashbot.transaction_isolation_drill`
- `schema_version=1`
- `evidence_boundary=software_proof_docker_transaction_isolation_gate`
- `production_ready=false`
- `overall_status=passed|failed`
- `transaction_invariant`：并发 command/status/ack 写入隔离语义是否成立。
- `cursor_invariant`：ACK cursor 不越过未完成命令。
- `ack_invariant`：ACK 不等于 delivery success。
- `concurrent_write_scenario`：记录本地构造的 interleaving，例如 command A pending、command B terminal ACK、status update interleaved、cursor remains before A。
- `not_proven`：必须包含真实生产 DB/queue、多实例一致性、真实生产 transaction isolation、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL、真实送达。
- `safe_summary` / `retry_hint`：仅普通用户或支持同学可读。
- `checksum`：用于 artifact 完整性校验；不得在 phone-safe summary 中原样暴露。

新增配置入口建议：

- `TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT`
- CLI：`--write-transaction-isolation-artifact <path>`
- CLI：`--transaction-isolation-artifact <path>`

Phone-safe summary：

- `/api/status.phone_readiness.transaction_isolation`
- `/api/diagnostics.transaction_isolation`
- `state=ready|missing|invalid|stale|failed`
- 不返回完整 artifact、checksum、local path、DB/queue URL、token、Authorization、OSS secret、AK/SK、root password、ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER 参数或 traceback。

## Task A / full-stack-software-engineer

### 允许改动范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- 对应 full-stack/operator tests
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/mobile_user_flow.md`
- 当前 sprint 的 `tech-done.md`，仅在 Task A 完成后记录实际改动和验证结果

范围外不得改动。不要触碰 remote bridge、ROS action、硬件配置、launch 参数或 unrelated docs。

### 实现要求

1. 在 `remote_cloud_relay.py` 增加 transaction isolation drill builder。
2. Drill 必须构造同一 robot 的并发/interleaved command/status/ack 场景：
   - command A 仍未 terminal ACK。
   - command B 后发或后处理并出现 terminal ACK。
   - status update 与 ACK 交错写入。
   - cursor 不得推进越过 command A。
   - ACK 不得被标记为 delivery success。
3. 增加 artifact validator 和 checksum 校验。
4. 增加 CLI 写 artifact 和 preflight 消费入口。
5. Preflight 有效消费后新增 `transaction_isolation=pass` check，但 `production_ready=false` 和生产缺口必须保持。
6. 在 operator status 与 diagnostics 中输出同一 phone-safe summary helper。
7. 文档同步更新 O6 proof ladder 和 phone-safe 字段说明。
8. 代码中的新增技术注释必须使用中文，并解释为什么要保守处理 cursor/ACK。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
```

```bash
PYTHONPATH=src/ros2_trashbot_behavior python3 -m ros2_trashbot_behavior.remote_cloud_relay --write-transaction-isolation-artifact /tmp/trashbot_transaction_isolation_drill.json
```

```bash
PYTHONPATH=src/ros2_trashbot_behavior TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT=/tmp/trashbot_transaction_isolation_drill.json python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

CLI smoke 期望输出包含：

```text
software_proof_ready=True
production_ready=False
transaction_isolation=pass
evidence_boundary=software_proof_docker_transaction_isolation_gate
```

```bash
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.12_23-24_remote-transaction-isolation-gate/tech-done.md
```

### 输出要求

Task A 必须返回：

1. 实际改动文件列表。
2. 上述验收命令输出片段。
3. 失败定位和修复记录，如有。
4. 剩余风险，特别是真实生产 DB/queue、多实例一致性、真实云/4G 未证明。

## Task B / robot-software-engineer

### 允许改动范围

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- 必要时 `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `docs/interfaces/ros_contracts.md`
- 当前 sprint 的 `tech-done.md`，仅在 Task B 完成后记录实际改动和验证结果

范围外不得改动。不要改 relay artifact、operator gateway、产品文档或硬件配置。

### 实现要求

1. 新增 remote bridge compatibility fence，模拟 cloud/status/diagnostics 中出现 transaction isolation metadata。
2. 验证 metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
3. 验证 metadata-only blocked response 不触发 robot action。
4. 验证 metadata-only blocked response 不发送 ACK。
5. 验证 metadata-only blocked response 不推进或持久化 cursor。
6. 验证 ACK 语义仍是 command envelope 处理证据，不是 delivery success。
7. 如需修复 `remote_bridge.py`，新增技术注释必须使用中文，并解释为什么 metadata 不应驱动 robot action。
8. 如接口文档需补充，更新 `docs/interfaces/ros_contracts.md`，明确 metadata 可被旧客户端忽略。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

```bash
git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py docs/interfaces/ros_contracts.md sprints/2026.05.12_23-24_remote-transaction-isolation-gate/tech-done.md
```

### 输出要求

Task B 必须返回：

1. 实际改动文件列表。
2. 上述验收命令输出片段。
3. 失败定位和修复记录，如有。
4. 剩余风险，特别是本轮没有真实 robot action、Nav2/fixed-route、WAVE ROVER 或 HIL。

## Product closeout

实现和验证完成后，由 `product-okr-owner` 更新：

- `OKR.md`
- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/tech-done.md`
- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/side2side_check.md`
- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/final.md`

Product closeout 验收命令：

```bash
git diff --check -- OKR.md sprints/2026.05.12_23-24_remote-transaction-isolation-gate/tech-done.md sprints/2026.05.12_23-24_remote-transaction-isolation-gate/side2side_check.md sprints/2026.05.12_23-24_remote-transaction-isolation-gate/final.md
```

本次规划阶段不要提前创建 `tech-done.md`、`side2side_check.md` 或 `final.md`。

## 并行启动要求

Task A 与 Task B 文件范围不重叠，后续进入 implementation 时必须在同一条消息中并行启动：

- `spawn_agent(agent_type=worker)` for `full-stack-software-engineer`
- `spawn_agent(agent_type=worker)` for `robot-software-engineer`

每个 worker prompt 必须包含对应 `.codex/agents/<role>.toml` 的完整 prompt、任务说明、文件范围、验收命令和输出要求。

## 本规划文件验收命令

```bash
git diff --check -- sprints/2026.05.12_23-24_remote-transaction-isolation-gate/pre_start.md sprints/2026.05.12_23-24_remote-transaction-isolation-gate/prd.md sprints/2026.05.12_23-24_remote-transaction-isolation-gate/tech-plan.md
```
