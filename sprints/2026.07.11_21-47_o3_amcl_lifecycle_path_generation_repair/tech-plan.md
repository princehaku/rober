# O3 AMCL Lifecycle Path Generation Repair Tech Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Execution mode: 单 owner 单线闭环

## 用户价值和本轮核心抓手

本轮核心抓手不是再证明 source/CLI 可用，也不是继续消费 O5 support-only，而是让真实板 no-motion localization/TF gate 从 `path_generation_requested=true` 推进到 planner-only path generation 可尝试的状态。只有把 `/amcl` lifecycle、fresh `/scan`/`/map`/`/amcl_pose`、dynamic `map->odom` 这几个门槛打通，后续 route execution、delivery/operator acceptance 和 HIL 才有现实入口。

## OKR 最低优先级核对

1. 当前最低 Objective：O5，完成度约 `85%`。
2. 本 sprint 是否直接针对该最低 Objective：`否`。
3. 不直接做 O5 的具体理由：
   - O5 当前缺口不是软件包装，而是明确的真实 production/external evidence：公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser。
   - 最近 O5 support-only lane 已固定 `okr_credit_allowed=false`，没有新 external material 时继续做 packet/readback 只会重复消费 blocker，不会产生 OKR 有效增量。
   - `19-46` 与 `20-46` 已把真实板 O3 no-motion lane 推进到新的 localization/path gate blocker；这是当前环境下最低风险、最接近 mission chain 的可执行抓手。
   - CEO 已明确要求每小时推进最低进度 OKR 时，不应在 O5 support-only fail-closed 后继续原地包装，而应转向 O3/O1 supporting no-motion localization/path readiness，为后续 Nav2 route execution / delivery / HIL 创造条件。

## Owner 与职责

- 责任 owner：`robot-algorithm-engineer`
- 负责到底：实现、验证、修复验证中发现的问题，并更新后续 `tech-done.md`
- Product 在本阶段只提供范围、优先级、验收口径和风险边界，不参与实现

## 目标分解

### 1. AMCL lifecycle clean active

目标：确认并修复 `/amcl` lifecycle inactive 问题，让 artifact 能明确区分：

- lifecycle 是否 active
- inactive 是 bringup、timing、probe 还是 runtime clean-up 问题

### 2. Signal freshness gate

目标：恢复或明确量化以下信号是否 fresh enough：

- `/scan`
- `/map`
- `/amcl_pose`

必须避免只报 topic type/publisher count；要能说明 sample/stamp/age 是否满足 localization gate。

### 3. Dynamic TF gate

目标：确认 `map->odom` 是否有 dynamic source，且 downstream `map->base_link` 是否因此 ready。

### 4. Planner-only path generation gate

目标：仅在 localization/TF gate ready 后，允许 planner-only `ComputePathToPose` attempt，并明确记录：

- `path_generation_requested`
- `path_generation_attempted`
- `path_generated`
- 若未 attempt，blocked reason 必须直指未满足的 gate

## 文件范围

后续 implementation 只允许在与本轮 owner 直接相关的算法/导航范围内改动；本计划文档阶段固定只落在本 sprint 目录。给 worker 的允许范围应以实现时实际任务为准，但接口边界必须保持以下约束：

- 允许触达：AMCL / map / TF / planner-only path generation 相关 helper、测试、导航文档和本 sprint 文档
- 不允许触达：O5 production stack、O6/O7 archive/UI、手机/Web/API、WAVE ROVER UART 控制链、`/api/base/manual`、真实运动控制

本轮计划文档文件：

- `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/pre_start.md`
- `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/prd.md`
- `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/tech-plan.md`

## 接口边界

- 允许：
  - lifecycle/map/AMCL/TF/readiness/probe
  - planner-only `ComputePathToPose` attempt
- 禁止：
  - 发布 `/cmd_vel`
  - 调用 `/api/base/manual`
  - 发送 NavigateToPose
  - 打开 WAVE ROVER UART
  - 任何会让 `safe_to_control`、`robot_control_executed`、`route_execution_success`、`delivery_success`、`hil_pass` 变成 true 的行为

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

只有当以下条件全部满足时，才允许进入 planner-only path generation attempt：

- `/amcl` lifecycle clean active
- `/scan` fresh enough
- `/map` observable
- `/amcl_pose` fresh enough
- dynamic `map->odom` observable
- downstream `map->base_link` 不再被 `map_to_odom` 阻塞

如果任一条件不满足，必须保持 `path_generation_attempted=false`，并把 blocked reason 写清楚。

## 验收命令

以下命令供 `robot-algorithm-engineer` 在 implementation/closeout 时直接复制执行，并供 Product 在收口时核验：

```bash
git diff --check -- sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|robot-algorithm-engineer|/amcl|/map|/scan|map->odom|path_generation|safe_to_control=false|NavigateToPose|/cmd_vel|/api/base/manual" sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair
```

## 验收标准

计划阶段验收：

- 三份文档存在且结构完整
- 明确写出 O5 不直接推进的理由
- 明确写出单 owner 为 `robot-algorithm-engineer`
- 明确写出 no-motion 强约束和 path generation gate

implementation 阶段验收：

- 不回退到旧 source/CLI blocker 叙事
- 至少把 `/amcl` lifecycle、signal freshness、dynamic TF 或 path gate 中的一层推进为更窄 root cause 或新的 attempted/generated 事实
- 任何 path attempt 都必须建立在 localization/TF gate ready 之后

## 风险与失败边界

- 最大风险是继续重复 `20-46` 的 root causes 而没有进一步缩窄，此时 closeout 必须明确说明为什么没有前进，不能包装成“bounded probe 已完成”。
- 第二风险是为追求 `path_generation_attempted=true` 而偷越 no-motion 边界，这会直接使证据失效。
- 第三风险是回头再修旧 source/CLI 或转去 O5 support-only，这两条都已被前两轮和当前记忆证明不是本轮正确抓手。
