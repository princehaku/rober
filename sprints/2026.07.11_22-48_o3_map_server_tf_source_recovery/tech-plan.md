# O3 Map Server TF Source Recovery Tech Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Execution mode: 单 owner 单线闭环

## 用户价值和本轮核心抓手

本轮核心抓手不是回头再修 O5 support-only，也不是重复证明 `/amcl active [3]`。当前最接近 mission chain 的可执行抓手，是把真实板 no-motion localization/TF gate 从 `path_generation_requested=true`、`path_generation_attempted=false` 推进到“前置门槛 ready 后允许 planner-only path attempt”。因此本轮聚焦两个前置 blocker：`map_server_active=false` 与 `tf_source_probe_not_executed`。

## OKR 最低优先级核对

1. 当前最低 Objective：O5，完成度约 `85%`。
2. 本 sprint 是否直接针对该最低 Objective：`否`。
3. 不直接做 O5 的具体理由：
   - O5 当前缺口不是软件包装，而是明确的真实 production/external evidence：公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser。
   - 最近 O5 support-only lane 已固定 `okr_credit_allowed=false`；没有新 external material 时继续做 wrapper/readback/support-only 只会重复消费 blocker，不会产生 OKR 有效增量。
   - `21-47` 已把 O3 no-motion chain 推进到 `/amcl active [3]`，当前最小可执行下一步就是拆开 `map_server_active=false` 与 `tf_source_probe_not_executed`，这是当前环境下最接近后续 path / route / delivery 链的实际抓手。
   - CEO 已明确要求此轮不要做 O5 support-only，不得发布 `/cmd_vel`、不得调用 `/api/base/manual`、不得发送 NavigateToPose、不得打开 WAVE ROVER UART。

## Owner 与职责

- 责任 owner：`robot-algorithm-engineer`
- 负责到底：实现、验证、修复验证中发现的问题，并更新后续 `tech-done.md`
- Product 在本阶段只提供范围、优先级、验收口径和风险边界，不参与实现

## 目标分解

### 1. Map server active gate

目标：确认并修复 `map_server_active=false` 的真实边界，让 artifact 能明确区分：

- lifecycle 未 active
- managed runtime 没有 clean start
- map source / map yaml / preflight 时序问题
- probe 或 cleanup 导致的假阴性

### 2. TF source probe gate

目标：恢复 TF source inventory，让 `tf_source_probe_not_executed` 不再是最终 blocked reason，而是变成：

- TF source 已执行且有具体 blocked reason
- 或 TF source 已确认可用

### 3. Localization freshness gate

目标：在 `/amcl active [3]` 已成立的前提下，恢复或量化：

- `/amcl_pose` 是否 fresh observed
- dynamic `map->odom` 是否出现
- `map->base_link` 是否不再被 `map_to_odom` 阻塞

### 4. Planner-only path generation gate

目标：仅在 localization/TF gate ready 后，允许 planner-only `ComputePathToPose` attempt，并明确记录：

- `path_generation_requested`
- `path_generation_attempted`
- `path_generated`
- 若未 attempt，blocked reason 必须直指未满足的 gate

## 文件范围

本轮计划文档阶段固定只落在当前 sprint 目录；后续 implementation 只允许在与本轮 owner 直接相关的算法/导航范围内改动。给 worker 的允许范围应以实现时实际任务为准，但接口边界必须保持以下约束：

- 允许触达：map_server / AMCL / TF source / planner-only path generation 相关 helper、测试、导航文档和本 sprint 文档
- 不允许触达：O5 production stack、O6/O7 archive/UI、手机/Web/API、WAVE ROVER UART 控制链、`/api/base/manual`、真实运动控制

本轮计划文档文件：

- `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/pre_start.md`
- `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/prd.md`
- `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/tech-plan.md`

## 接口边界

- 允许：
  - map_server / AMCL / TF source / readiness / probe
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

- `map_server_active=true`
- `/amcl` lifecycle clean active
- TF source probe 已执行且可支撑 dynamic `map->odom`
- `/amcl_pose` fresh observed
- `map_to_odom_dynamic.observed=true`
- `map->base_link` 不再被 `map_to_odom` 阻塞

如果任一条件不满足，必须保持 `path_generation_attempted=false`，并把 blocked reason 写清楚。

## 验收命令

计划阶段验收命令如下：

```bash
git diff --check -- sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|map_server_active=false|tf_source_probe_not_executed|path_generation_attempted=false|path_generated=false|safe_to_control=false|robot-algorithm-engineer" sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery
```

后续 implementation/closeout 应继续由 owner 执行并补充更细的验证命令。

## 验收标准

计划阶段验收：

- 三份文档存在且结构完整
- 明确写出 O5 不直接推进的理由
- 明确写出单 owner 为 `robot-algorithm-engineer`
- 明确写出 `map_server_active=false`、`tf_source_probe_not_executed`、`path_generation_attempted=false`、`path_generated=false` 与 no-motion 强约束

implementation 阶段验收：

- 不回退到单纯重复 `/amcl active [3]` 的叙事
- 至少把 map_server、TF source、`/amcl_pose` freshness、dynamic `map->odom` 或 path gate 中的一层推进为更窄 root cause 或新的 attempted/generated 事实
- 任何 path attempt 都必须建立在 localization/TF gate ready 之后

## 风险与失败边界

- 最大风险是继续重复 `21-47` 的 root causes 而没有进一步缩窄，此时 closeout 必须明确说明为什么没有前进，不能包装成“supporting lane 已推进”。
- 第二风险是为追求 `path_generation_attempted=true` 而偷越 no-motion 边界，这会直接使证据失效。
- 第三风险是 TF source probe 仍然不执行，导致 `map->odom` 与 `map->base_link` 继续停留在推断层，而不是 source-inventory 结论层。
