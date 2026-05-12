# Sprint 2026.05.12_25-26 Remote Production Recovery Gate - Tech Plan

## 状态

- 阶段：tech-plan
- Product Owner：`product-okr-owner`
- 主线 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- 目标证据：`software_proof_docker_production_recovery_gate`
- 执行模式：team execution；Task A 与 Task B 文件范围基本不重叠，可并行启动。

## 技术目标

新增 Docker/local production recovery gate。它必须生成和消费 `trashbot.production_recovery_gate` artifact/preflight/phone-safe summary，把 production backup/disaster recovery 的上线前置缺口做成可执行、可解释、可阻断的 gate。

本轮保持 `production_ready=false` 和 `overall_status=blocked`，明确不等于真实生产 DB/queue、真实生产备份、真实灾备、多实例一致性、真实云、真实 4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 接口和证据边界

新增 artifact contract：

- `schema=trashbot.production_recovery_gate`
- `schema_version=1`
- `evidence_boundary=software_proof_docker_production_recovery_gate`
- `production_ready=false`
- `overall_status=blocked`
- `local_backup_restore_status`：Docker/local backup/restore 或恢复演练是否有可校验输入。
- `recovery_drill_status`：本地 recovery gate 是否完成 schema/checksum/invariant 校验。
- `production_backup_policy_status`：真实生产备份策略状态，当前必须是 blocked/not_proven。
- `disaster_recovery_status`：真实灾备恢复状态，当前必须是 blocked/not_proven。
- `state_backend_status`：file/SQLite proof store 与生产 DB/queue 的边界。
- `db_queue_status`：生产 DB/queue 是否真实接入，当前必须是 blocked/not_proven。
- `multi_instance_status`：多实例一致性是否真实验证，当前必须是 blocked/not_proven。
- `retention_status` / `restore_objective_status`：保留周期、RPO/RTO 或恢复目标的产品状态。
- `not_proven`：必须包含真实生产 DB/queue、多实例一致性、真实生产备份策略、真实灾备恢复、真实云、真实 4G/SIM、真实 OSS upload、CDN origin fetch、Nav2/fixed-route、WAVE ROVER/HIL、真实送达。
- `safe_summary` / `retry_hint`：仅普通用户或支持同学可读。
- `checksum`：用于 artifact 完整性校验；不得在 phone-safe summary 中原样暴露。

新增配置入口建议：

- `TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT`
- CLI：`--write-production-recovery-artifact <path>`
- CLI：`--production-recovery-artifact <path>`

Phone-safe summary：

- `/api/status.phone_readiness.production_recovery`
- `/api/diagnostics.production_recovery`
- `state=ready|missing|invalid|stale|failed|blocked`
- 不返回完整 artifact、checksum、local path、DB/queue URL、token、Authorization、OSS secret、AK/SK、root password、ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER 参数或 traceback。

## Task A / full-stack-software-engineer

### 允许改动范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/mobile_user_flow.md`
- 当前 sprint 的 `tech-done.md`，仅在 Task A 完成后记录实际改动和验证结果

范围外不得改动。不要触碰 `remote_bridge.py`、ROS action、硬件配置、launch 参数或 unrelated docs。

### 实现要求

1. 在 `remote_cloud_relay.py` 增加 production recovery gate builder。
2. Builder 必须把 Docker/local recovery proof 与真实 production DR 明确分层：
   - 本地 artifact/schema/checksum 可通过。
   - 真实 production backup policy 仍未证明。
   - 真实 disaster recovery 仍未证明。
   - 生产 DB/queue、多实例一致性、真实云/4G/OSS/CDN 仍未证明。
   - `production_ready=false`、`overall_status=blocked` 必须保持。
3. 增加 artifact validator 和 checksum 校验。
4. 增加 CLI 写 artifact 和 preflight 消费入口。
5. Preflight 有效消费后新增 `production_recovery=pass` 或等价 check，但总体仍 blocked。
6. 在 operator status 与 diagnostics 中输出同一 phone-safe summary helper。
7. 文档同步更新 O6 proof ladder 和 phone-safe 字段说明。
8. 代码中的新增技术注释必须使用中文，并解释为什么不能把本地恢复演练当作真实生产灾备。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
```

```bash
PYTHONPATH=src/ros2_trashbot_behavior python3 -m ros2_trashbot_behavior.remote_cloud_relay --write-production-recovery-artifact /tmp/trashbot_production_recovery_gate.json
```

```bash
PYTHONPATH=src/ros2_trashbot_behavior TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT=/tmp/trashbot_production_recovery_gate.json python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

CLI/preflight smoke 期望输出包含：

```text
software_proof_ready=True
production_ready=False
overall_status=blocked
production_recovery=pass
evidence_boundary=software_proof_docker_production_recovery_gate
```

```bash
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.12_25-26_remote-production-recovery-gate/tech-done.md
```

### 输出要求

Task A 必须返回：

1. 实际改动文件列表。
2. 上述验收命令输出片段。
3. 失败定位和修复记录，如有。
4. 剩余风险，特别是真实生产 DB/queue、生产备份/灾备、多实例一致性、真实云/4G 未证明。

## Task B / robot-software-engineer

### 允许改动范围

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `docs/interfaces/ros_contracts.md`
- 当前 sprint 的 `tech-done.md`，仅在 Task B 完成后记录实际改动和验证结果
- 只有发现生产 `remote_bridge.py` 必须改才能保持兼容时，才允许改 `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`，并必须在返回和 `tech-done.md` 写清兼容风险、原因和验证证据

范围外不得改动。不要改 relay artifact、operator gateway、产品文档或硬件配置。

### 实现要求

1. 新增 remote bridge compatibility fence，模拟 cloud/status/diagnostics 中出现 production recovery metadata。
2. 验证 metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
3. 验证 metadata-only blocked response 不触发 robot action。
4. 验证 metadata-only blocked response 不发送 ACK。
5. 验证 metadata-only blocked response 不推进或持久化 cursor。
6. 验证 ACK 语义仍是 command envelope 处理证据，不是 delivery success，也不是 production recovery 完成证据。
7. 如需修复 `remote_bridge.py`，新增技术注释必须使用中文，并解释为什么 metadata 不应驱动 robot action。
8. 更新 `docs/interfaces/ros_contracts.md`，明确 production recovery metadata 可被旧客户端忽略，且不属于 robot command envelope。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

```bash
git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/interfaces/ros_contracts.md src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py sprints/2026.05.12_25-26_remote-production-recovery-gate/tech-done.md
```

### 输出要求

Task B 必须返回：

1. 实际改动文件列表。
2. 上述验收命令输出片段。
3. 失败定位和修复记录，如有。
4. 剩余风险，特别是本轮没有真实 robot action、Nav2/fixed-route、WAVE ROVER 或 HIL。

## Task C / product-okr-owner

### 允许改动范围

- `OKR.md`
- `sprints/2026.05.12_25-26_remote-production-recovery-gate/tech-done.md`
- `sprints/2026.05.12_25-26_remote-production-recovery-gate/side2side_check.md`
- `sprints/2026.05.12_25-26_remote-production-recovery-gate/final.md`

### closeout 要求

1. 汇总 Task A 和 Task B 的实际改动、验证输出、失败定位和剩余风险。
2. 保守更新 O6 进度；不得把 Docker/local gate 写成真实 production backup/disaster recovery。
3. 明确 O5 不因本轮增加真实手机/production app 进度。
4. 明确 O1/O2/O3/O4 不因本轮增加硬件、导航、相机或 HIL 进度。
5. 核对 docs/product 和 docs/interfaces 路径存在且已同步。

### Product closeout 验收命令

```bash
test -f docs/product/cloud_4g_infrastructure.md && test -f docs/product/remote_4g_mvp.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
```

```bash
git diff --check -- OKR.md sprints/2026.05.12_25-26_remote-production-recovery-gate/tech-done.md sprints/2026.05.12_25-26_remote-production-recovery-gate/side2side_check.md sprints/2026.05.12_25-26_remote-production-recovery-gate/final.md
```

本次规划阶段不要提前创建 `tech-done.md`、`side2side_check.md` 或 `final.md`。

## 并行启动要求

Task A 与 Task B 文件范围不重叠，后续进入 implementation 时必须在同一条消息中并行启动：

- `spawn_agent(agent_type=worker)` for `full-stack-software-engineer`
- `spawn_agent(agent_type=worker)` for `robot-software-engineer`

每个 worker prompt 必须包含对应 `.codex/agents/<role>.toml` 的完整 prompt、任务说明、文件范围、验收命令和输出要求。

## 本规划文件验收命令

```bash
test -f sprints/2026.05.12_25-26_remote-production-recovery-gate/pre_start.md && test -f sprints/2026.05.12_25-26_remote-production-recovery-gate/prd.md && test -f sprints/2026.05.12_25-26_remote-production-recovery-gate/tech-plan.md
```

```bash
git diff --check -- sprints/2026.05.12_25-26_remote-production-recovery-gate/pre_start.md sprints/2026.05.12_25-26_remote-production-recovery-gate/prd.md sprints/2026.05.12_25-26_remote-production-recovery-gate/tech-plan.md
```
