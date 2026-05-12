# Sprint 2026.05.12_21-22 Remote Queue Ordering Drill - Tech Plan

## 状态

- 阶段：tech-plan
- 主责：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- Product closeout：`product-okr-owner`
- Evidence boundary：`software_proof_docker_queue_ordering_drill`

## 接口和边界

- 新增 queue ordering metadata 只能作为 artifact、preflight、status 或 diagnostics 摘要出现。
- 不改变 `trashbot.remote.v1` command/status/ack envelope。
- ACK 仍只表示 command accepted/processing evidence，不表示 delivery success。
- metadata-only blocked response 不得触发 robot action，不得推进或持久化 cursor。
- 本轮不得声明真实云、真实 4G、真实生产 DB/queue、多实例一致性、transaction isolation、备份/灾备、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## Task A - Full-stack / Remote Queue Ordering Drill

### Owner

`full-stack-software-engineer`

### 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `.env.example`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.12_21-22_remote-queue-ordering-drill/tech-done.md`

### 实现要求

- 新增 `trashbot.queue_ordering_drill` artifact，包含 schema、schema_version、evidence_boundary、ordering/concurrency/cursor/ACK invariant、not_proven、safe_summary、retry_hint、updated_at 和 checksum。
- 新增 CLI 或等价入口生成 queue ordering drill artifact，建议覆盖并发提交、相邻 command id、`cmd-9` / `cmd-10` 顺序和 stale/invalid artifact。
- preflight 新增 `queue_ordering_drill` check；有效 artifact 只代表 Docker/local software proof，必须保持 `production_ready=false`。
- `/api/status.phone_readiness.queue_ordering_drill` 与 `/api/diagnostics.queue_ordering_drill` 输出 phone-safe summary，覆盖 `ready|missing|invalid|stale|failed`。
- `.env.example` 只新增占位变量，例如 `TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT`，不得包含真实密钥、DB URL、queue URL 或账号。
- 同步 `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md`，明确本轮不证明真实生产队列。
- 更新本 sprint `tech-done.md`，记录实际改动、验证输出、偏差和剩余风险。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py .env.example docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.12_21-22_remote-queue-ordering-drill/tech-done.md
```

## Task B - Robot Compatibility Fence

### Owner

`robot-software-engineer`

### 文件范围

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`，仅当兼容性围栏暴露真实问题时允许修改。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`，仅当 protocol helper 需要最小修复时允许修改。
- `sprints/2026.05.12_21-22_remote-queue-ordering-drill/tech-done.md`

### 验收要求

- 优先只新增或调整测试围栏；没有真实兼容性缺口时不改生产代码。
- 确认新增 queue ordering metadata 不改变 `trashbot.remote.v1` command/status/ack envelope。
- 确认 ACK 不等于 delivery success。
- 确认 metadata-only blocked/invalid/stale response 不触发本地 action。
- 确认 metadata-only response 不推进或持久化 cursor。
- 确认 command ordering metadata 不要求 robot bridge 依赖字符串排序或生产队列实现细节。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py sprints/2026.05.12_21-22_remote-queue-ordering-drill/tech-done.md
```

## Product Closeout

### Owner

`product-okr-owner`

### 文件范围

- `sprints/2026.05.12_21-22_remote-queue-ordering-drill/side2side_check.md`
- `sprints/2026.05.12_21-22_remote-queue-ordering-drill/final.md`
- `OKR.md`

### 收口要求

- 只在 Task A 和 Task B 返回验证证据后执行。
- `side2side_check.md` 对照 PRD 和 tech-plan，核对 evidence boundary、接口不变性、phone-safe 摘要和剩余缺口。
- `final.md` 写清 O6 是否可保守提升；若只有 Docker/local queue ordering drill，必须明确仍不等于真实生产 DB/queue。
- `OKR.md` 只做保守更新，不提升 O1/O2/O3/O4/O5。

### 验收命令

```bash
git diff --check -- OKR.md sprints/2026.05.12_21-22_remote-queue-ordering-drill/side2side_check.md sprints/2026.05.12_21-22_remote-queue-ordering-drill/final.md
```

## 并行执行规则

- Task A 和 Task B 文件范围互不重叠，下一阶段应并行派发 `full-stack-software-engineer` 和 `robot-software-engineer`。
- 两个 Engineer 都必须更新同一个 `tech-done.md` 时，以 Task A 先创建结构、Task B 追加兼容性证据为准；不得覆盖对方记录。
- Product closeout 等两条工程证据返回后再执行。

## 本轮计划验收命令

```bash
git diff --check -- sprints/2026.05.12_21-22_remote-queue-ordering-drill/pre_start.md sprints/2026.05.12_21-22_remote-queue-ordering-drill/prd.md sprints/2026.05.12_21-22_remote-queue-ordering-drill/tech-plan.md
```
