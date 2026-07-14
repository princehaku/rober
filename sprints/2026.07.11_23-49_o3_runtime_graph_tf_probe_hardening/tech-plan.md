# O3 Runtime Graph TF Probe Hardening Tech Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Execution mode: 单 owner 单线闭环

## 用户价值和本轮核心抓手

本轮核心抓手不是回头再修 O5 support-only，也不是重复证明 `managed_runtime_started=true`。当前最接近 mission chain 的可执行抓手，是把真实板 no-motion localization/TF gate 从“runtime 已启动但 wait graph / AMCL inventory / TF source 仍不可靠”推进到“前置门槛 ready 后允许 planner-only path attempt”。因此本轮聚焦三个前置 blocker：`managed_runtime_wait_timeout`、`rclpy_node_names_failed` 和 `/tf_topic_missing`，并把 AMCL rclpy import chain 作为必须收窄的 runtime blocker。

## OKR 最低优先级核对

1. 当前最低 Objective：O5，完成度约 `85%`。
2. 本 sprint 是否直接针对该最低 Objective：`否`。
3. 不直接做 O5 的具体理由：
   - O5 当前缺口不是软件包装，而是明确的真实 production/external evidence：公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser。
   - 最近 O5 support-only lane 已固定 `okr_credit_allowed=false`；没有新 external material 时继续做 wrapper/readback/support-only 只会重复消费 blocker，不会产生 OKR 有效增量。
   - `22-48` 已把 O3 no-motion chain 推进到 `board_source_preflight_ready`、`cli_ready=true`、`runtime_ready=true` 和 `managed_runtime_started=true`；当前最小可执行下一步就是硬化 runtime graph、AMCL inventory runtime 和 TF source fallback，这是当前环境下最接近后续 path / route / delivery 链的实际抓手。
   - CEO 已明确要求本轮继续 O3/O1 no-motion lane，但不能重复包装 `22-48`，且 gate ready 前不允许 planner-only path attempt。

## Owner 与职责

- 责任 owner：`robot-algorithm-engineer`
- 负责到底：实现、验证、修复验证中发现的问题，并更新后续 `tech-done.md`
- Product 在本阶段只提供范围、优先级、验收口径和风险边界，不参与实现

## 本轮核心抓手

- 抓手 1：修/硬化 board-side managed runtime wait graph probe，优先解释 `managed_runtime_wait_timeout`
- 抓手 2：修/替换 graph node inventory runtime，优先解释 `rclpy_node_names_failed`
- 抓手 3：修/硬化 TF source probe fallback，并同时收窄 AMCL rclpy inventory runtime 的 `librcl_action.so` / `_rclpy_pybind11` import chain
- 抓手 4：仅在以上 gate ready 后，允许 planner-only `ComputePathToPose` attempt

## 目标分解

### 1. Managed runtime wait graph probe

目标：确认并修复 `managed_runtime_wait_timeout` 的真实边界，让 artifact 能明确区分：

- runtime 已启动但 graph inventory timeout
- lifecycle 实际未 ready
- source / shell / ROS 环境衔接问题
- probe 自身 timeout 或 cleanup 导致的假阴性

### 2. Node graph inventory runtime

目标：恢复或替换 node graph inventory，让 `rclpy_node_names_failed` 不再是最终 blocked reason，而是变成：

- 已执行并得到具体 runtime blocked reason
- 或 inventory 已确认可用

### 3. AMCL rclpy inventory runtime

目标：把 `librcl_action.so` / `_rclpy_pybind11` import chain 收敛成可复验的 runtime 路径，让 artifact 能明确区分：

- import/runtime 依赖问题
- shell/source 环境问题
- inventory probe 代码路径问题
- 与 TF source probe 共享的 runtime blocker

### 4. TF source probe fallback

目标：恢复 TF source inventory，让 `/tf_topic_missing` 不再只是最终缺失结论，而是变成：

- TF source probe 已执行且有具体 blocked reason
- 或 TF source 已确认可用

### 5. Planner-only path generation gate

目标：仅在 runtime graph、AMCL inventory 与 TF source gate ready 后，允许 planner-only `ComputePathToPose` attempt，并明确记录：

- `path_generation_requested`
- `path_generation_attempted`
- `path_generated`
- 若未 attempt，blocked reason 必须直指未满足的 gate

## 文件范围

本轮计划文档阶段固定只落在当前 sprint 目录；后续 implementation 只允许在与本轮 owner 直接相关的算法/导航范围内改动。

给 Algorithm worker 的允许改动范围：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/tech-done.md`
- 本 sprint 运行中新增的 local/live artifacts（仅限本轮相关产物）

不允许触达：

- O5 production stack
- O6/O7 archive/UI
- 手机/Web/API
- WAVE ROVER UART 控制链
- `/api/base/manual`
- 真实运动控制

本轮计划文档文件：

- `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/pre_start.md`
- `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/prd.md`
- `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/tech-plan.md`

## 接口边界

- 允许：
  - managed runtime / graph / map_server / AMCL / TF source / readiness / probe
  - planner-only `ComputePathToPose` attempt
- 禁止：
  - 发布 `/cmd_vel`
  - 调用 `/api/base/manual`
  - 发送 NavigateToPose
  - 打开 WAVE ROVER UART
  - 任何会让 `safe_to_control=false` 以外的 safety/control/HIL/delivery 字段变成 true 的行为

## No-Motion 强约束

后续 worker 必须在所有 artifact 和 closeout 中继续固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

只有当以下条件全部满足时，才允许进入 planner-only `ComputePathToPose` attempt：

- `managed_runtime_wait_timeout` 已被收敛为非阻塞状态
- node graph inventory 不再停在 `rclpy_node_names_failed`
- AMCL inventory runtime 不再停在 `librcl_action.so` / `_rclpy_pybind11` import chain
- TF source probe 已执行且可支撑 dynamic `map->odom`
- `map_server_active=true`
- `amcl_active=true`
- `amcl_pose_observed=true`
- `map_to_odom_dynamic.observed=true`
- `map->base_link` 不再被 `map_to_odom` 阻塞

如果任一条件不满足，必须保持 `path_generation_attempted=false`，并把 blocked reason 写清楚。

## 验收命令

计划阶段验收命令如下：

```bash
git diff --check -- sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|managed_runtime_wait_timeout|rclpy_node_names_failed|/tf_topic_missing|librcl_action.so|path_generation_attempted=false|path_generated=false|safe_to_control=false|robot-algorithm-engineer" sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening
```

后续 implementation 阶段给 `robot-algorithm-engineer` 的验收命令：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening
```

## 验收标准

计划阶段验收：

- 三份文档存在且结构完整
- 明确写出 O5 不直接推进的理由
- 明确写出单 owner 为 `robot-algorithm-engineer`
- 明确写出 `managed_runtime_wait_timeout`、`rclpy_node_names_failed`、`/tf_topic_missing`、`librcl_action.so`、`path_generation_attempted=false`、`path_generated=false` 与 no-motion 强约束
- 明确给出 Algorithm worker 的文件范围和验收命令

implementation 阶段验收：

- 不回退到单纯重复 `22-48` partial artifact 的叙事
- 至少把 runtime graph、node inventory、AMCL inventory runtime、TF source 或 path gate 中的一层推进为更窄 root cause 或新的 attempted/generated 事实
- 任何 path attempt 都必须建立在 gate ready 之后

## 风险与失败边界

- 最大风险是继续重复 `22-48` 的 root causes 而没有进一步缩窄，此时 closeout 必须明确说明为什么没有前进，不能包装成“supporting lane 已推进”。
- 第二风险是为追求 `path_generation_attempted=true` 而偷越 no-motion 边界，这会直接使证据失效。
- 第三风险是 graph inventory、AMCL inventory runtime 与 TF source fallback 共享同一运行时依赖问题，导致多个 probe 一起停在 runtime 层；若发生，必须把共享 blocker 写清楚，而不是分别重复包装。
