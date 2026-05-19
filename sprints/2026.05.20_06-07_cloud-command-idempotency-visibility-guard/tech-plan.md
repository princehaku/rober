# Sprint 2026.05.20_06-07 Cloud Command Idempotency Visibility Guard - Tech Plan

## 1. 计划状态

- sprint_type: epic
- 主题：`cloud_command_idempotency_visibility_guard`
- 本文件状态：planning only，当前任务只创建计划，不实现产品代码。
- 目标证据边界：`software_proof_docker_cloud_command_idempotency_visibility_guard`

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 68%。
2. 本 sprint 是否针对最低 Objective：是，针对 Objective 5 的 command/status/ack 幂等安全可见性。
3. 为什么不提高 Objective 5 completion：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser。它只能形成 Docker/local software proof。
4. Objective 1 核对：PR #5 `PRRT_kwDOSWB9286CJ3tQ`、`PRRT_kwDOSWB9286CJ3tU` 已 resolved，但 `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false`，真实 2D LiDAR / ToF 和 HIL materials 仍缺。本轮不关闭 O1 缺口，不提高 O1 completion。
5. 重复 blocker 红线：近期 O5 已完成 `cloud_ack_outage_replay_guard`、`cloud_pending_ack_status_guard`、`cloud_command_expiry_safety_guard`。本轮不是继续包装 external proof blocker，而是推进现有 duplicate command cached ACK 行为的可见功能安全。

## 3. 技术目标

把重复 command id 的现有 cached ACK 行为扩展为可见、可诊断、fail-closed 的跨端状态：

- Robot 不重复提交本地 action。
- Robot/operator status 明确输出 duplicate/deduped 状态。
- mobile/web 明确展示“重复云指令已去重，不代表 delivery success”。
- docs/product 明确 command idempotency visibility contract。

建议状态字段：

```text
degradation_state=command_duplicate_deduped
duplicate_command_id=<safe command id or [redacted]>
cached_ack_state=<acked|failed|ignored>
ack_semantics=duplicate_cached_ack_not_delivery_success
remote_ready=false
primary_actions_enabled=false
retry_hint=refresh_status
proof_boundary=software_proof_docker_cloud_command_idempotency_visibility_guard
```

字段名允许由 `robot-software-engineer` 在实现时按现有 schema 最小调整，但必须保留同等语义并在 tests/docs 中可 grep。

## 4. Owner / File Split

### 4.1 `robot-software-engineer`

允许改动范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/remote_4g_mvp.md`

任务：

- 在 duplicate command cached ACK 路径输出 phone-safe duplicate/deduped status。
- 保持 duplicate command 不重复调用 backend action。
- 明确 pending ACK / expired command / duplicate deduped 的优先级；pending ACK 和 expired command 不得被 duplicate 状态遮盖。
- 增加或更新 focused unittest，覆盖 duplicate status、redaction、`delivery_success` 否定边界。
- 同步 `docs/product/remote_4g_mvp.md`。

### 4.2 `full-stack-software-engineer`

允许改动范围：

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_idempotency_visibility_guard.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

任务：

- 新增或复用 cloud readiness / command safety panel，展示 duplicate/deduped read-only copy。
- Start Delivery、Confirm Dropoff、Cancel 在该状态下保持 disabled。
- 文案必须中文优先：重复云指令已去重；机器人没有重复执行；这不是送达成功。
- 不新增自动重放、自动 resubmit 或控制 endpoint。
- 同步 `docs/product/mobile_user_flow.md`。

### 4.3 `product-okr-owner`

允许改动范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard/tech-done.md`
- `sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard/side2side_check.md`
- `sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard/final.md`

任务：

- 验收 Robot 和 Full-Stack 证据。
- 保守同步 OKR/progress log：Objective 5、Objective 4、Objective 1 completion 不因本轮 software proof 提升。
- closeout 必须写清 `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false`，以及本轮不证明 delivery success。

## 5. 并行启动计划

Implementation 阶段应并行启动 3 个子 agent：

- `robot-software-engineer`：主责 Robot/operator contract 与 focused tests。
- `full-stack-software-engineer`：主责 mobile/web fixture/UI/test 与 product mobile doc。
- `product-okr-owner`：只读跟踪 implementation 输出，待两个 engineer 返回后做 closeout；不得抢工程实现。

Robot 与 Full-Stack 文件范围互不重叠，必须并行启动。Product closeout 与工程实现有阶段依赖，可在 engineer 返回后收口。

## 6. 接口影响

- 不新增 cloud endpoint。
- 不改变 command idempotency key 语义。
- 不改变 ACK terminal state 枚举的真实含义；只新增或补齐 duplicate/deduped visibility。
- mobile/web 只消费已有 `/api/status`、`/api/diagnostics` 安全字段或 Robot/status safe summary。
- 不暴露 `/cmd_vel`、ROS topic、serial/UART、baudrate、WAVE ROVER 参数、credentials、DB/queue URL、local path、traceback、raw artifacts、delivery success claims。

## 7. 验收命令

### 7.1 Planning 本轮已要求执行

```bash
test -f sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard/pre_start.md && test -f sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard/prd.md && test -f sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard/tech-plan.md
```

```bash
rg -n "sprint_type: epic|cloud_command_idempotency_visibility_guard|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_command_idempotency_visibility_guard|OKR 最低优先级核对|robot-software-engineer|full-stack-software-engineer|product-okr-owner" sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard
```

```bash
git diff --check -- sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard
```

### 7.2 Robot implementation 围栏

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
```

```bash
rg -n "command_duplicate_deduped|duplicate_cached_ack_not_delivery_success|software_proof_docker_cloud_command_idempotency_visibility_guard|primary_actions_enabled=false|delivery success" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md
```

### 7.3 Full-Stack implementation 围栏

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/web/test_mobile_web_entrypoint.py
```

```bash
node --check mobile/web/app.js
```

```bash
rg -n "command_duplicate_deduped|duplicate_cached_ack_not_delivery_success|software_proof_docker_cloud_command_idempotency_visibility_guard|重复云指令|送达成功" mobile/web docs/product/mobile_user_flow.md
```

### 7.4 Product closeout 围栏

```bash
rg -n "cloud_command_idempotency_visibility_guard|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_command_idempotency_visibility_guard|delivery success|真实公网 HTTPS/TLS|4G/SIM|production DB/queue" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/fixtures/robot_diagnostics_cloud_command_idempotency_visibility_guard.json mobile/web/test_mobile_web_entrypoint.py sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard
```

## 8. 风险和回退

- 风险：duplicate status 与 pending ACK status 混淆。回退策略：pending ACK 优先，因为本地 terminal ACK 尚未被云端确认；duplicate visibility 只在 cached ACK 已可安全复用时展示。
- 风险：mobile copy 让用户以为任务完成。回退策略：文案强制包含“不是送达成功”，并用 tests/rg 检查 `delivery success` 否定边界。
- 风险：状态字段过多导致接口漂移。回退策略：优先复用 existing remote readiness / command safety summary，新增字段只做 phone-safe metadata。

## 9. 完成定义

- Robot、Full-Stack、Product 三方围栏通过。
- `tech-done.md`、`side2side_check.md`、`final.md` 补齐。
- `OKR.md` 与 `docs/process/okr_progress_log.md` 保守同步。
- Objective 5 保持约 68%，Objective 1 保持约 81%，Objective 4 保持约 99%，除非真实 external/hardware/phone evidence 另行到位。
- closeout 明确本轮不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser、WAVE ROVER/UART/HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success。
