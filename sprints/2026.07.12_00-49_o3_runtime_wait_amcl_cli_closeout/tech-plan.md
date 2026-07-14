# O3 Runtime Wait AMCL CLI Closeout Tech Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Execution mode: 单 owner 单线闭环

## 用户价值和本轮核心抓手

用户价值是让机器人送垃圾主链路离 current same-run path generation 和 Nav2 route execution 更近。本轮不再重复“fallback 已执行”，而是要求 `robot-algorithm-engineer` 把 true-board managed runtime wait 自然收口为 final `managed_runtime_wait_result`，消费 AMCL CLI fallback live closeout，并在 gate 未 ready 前继续保持 no-motion 与 `path_generation_attempted=false`、`path_generated=false`。

## OKR 最低优先级核对

1. 当前最低 Objective：O5，完成度约 `85%`。
2. 本 sprint 是否直接针对该最低 Objective：`否`。
3. 不直接做 O5 的具体理由：
   - O5 的有效缺口是公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 等 external evidence，不是更多本地 wrapper、packet、readback 或 readiness summary。
   - 最近 O5 support-only 已固定 `okr_credit_allowed=false`；没有新 external evidence 时继续消费 O5 blocker，不会带来 OKR 有效增量。
   - O1/O6/O7 当前约 `93%`，但 O1 仍缺 current same-run path generation success 与 Nav2 route execution success。O3 no-motion runtime wait / AMCL CLI closeout 是当前环境中最接近 O1 mission chain 的可执行前置链路。
   - CEO 已明确要求本轮不要回到 O5，也不要重复写“fallback 已执行”作为新进展；本轮应聚焦 final `managed_runtime_wait_result`、AMCL CLI fallback closeout 和 no-motion path gate。

## Owner 与职责

- 责任 owner：`robot-algorithm-engineer`
- 负责到底：实现、验证、修复验证中发现的问题，并更新后续 `tech-done.md`
- Product 负责本计划、边界、验收口径和后续 closeout，不参与算法实现

## 目标分解

### 1. True-board managed runtime wait final closeout

目标：让 helper 自然写出 final `managed_runtime_wait_result`，不能只停在 `partial_runtime_in_progress` 的 `current_command.command=ros2 node list`。

必须明确区分：

- `ros2_node_list_timeout`
- `ros2_node_list_empty_after_wait`
- node graph visible but lifecycle inactive
- managed runtime process still active but graph not observable
- helper timeout/cleanup 造成的 partial artifact

### 2. `ros2 node list` fallback 归因

目标：消费 `23-49` 已证明会执行的 fallback，让 artifact 记录最终 boundary，而不只是记录 fallback 当前正在跑。

验收字段建议：

- fallback 是否执行
- fallback returncode / timeout / stdout / stderr 摘要
- node graph 是否 observed
- 若 observed，`/map_server`、`/amcl` 是否可见
- 若未 observed，blocked reason 是否比 `TimeoutExpired` current command 更窄

### 3. AMCL CLI fallback live closeout

目标：让 AMCL CLI fallback 在 true-board artifact 中形成 closeout，不再只停留在代码和单测层。

必须覆盖：

- `/amcl` node info 或明确 node not observed
- `/tf` topic info 或明确 topic not observed
- `/tf_static` topic info 或明确 topic not observed
- AMCL param probe 的结果或明确 blocked reason
- `probe_mode=ros2_cli_fallback` 或等价 live closeout 字段

### 4. Planner-only path generation gate

目标：gate 未 ready 前继续保持 `path_generation_attempted=false`、`path_generated=false`；只有全部前置条件满足后，才允许 planner-only `ComputePathToPose` attempt。

前置条件：

- final `managed_runtime_wait_result` 非阻塞或有足够 graph visibility
- `map_server_active=true`
- `amcl_active=true`
- `amcl_pose_observed=true`
- AMCL CLI fallback closeout 支持 `/tf` / `/tf_static` / `/amcl` inventory
- `map_to_odom_dynamic.observed=true`
- `map_to_base_link` 不再被 missing `map_to_odom` 阻塞

## 文件范围

本轮 Product 初始三文档只允许改动：

- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/pre_start.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/prd.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/tech-plan.md`

给 Algorithm worker 的允许改动范围：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/tech-done.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/side2side_check.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/final.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/artifacts/`

不允许触达：

- `OKR.md`，除非后续 final closeout 由 Product 明确判断需要更新
- `docs/process/okr_progress_log.md`，除非后续 final closeout 由 Product 明确判断需要更新
- O5 production stack
- O6/O7 archive/UI
- 手机/Web/API
- WAVE ROVER UART 控制链
- `/api/base/manual`
- 真实运动控制

## 接口边界

允许：

- managed runtime wait graph closeout
- `ros2 node list` / node graph 只读诊断
- map_server / AMCL lifecycle 只读诊断
- AMCL CLI fallback inventory
- `/tf`、`/tf_static`、`/amcl` topic/node/param 只读诊断
- gate ready 后的 planner-only `ComputePathToPose` attempt

禁止：

- 发布 `/cmd_vel`
- 调用 `/api/base/manual`
- 发送 NavigateToPose
- 打开 WAVE ROVER UART
- 让真实底盘运动
- 把 `safe_to_control=false` 以外的 safety/control/HIL/delivery 字段改成 true

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

gate 未 ready 时必须固定：

- `path_generation_attempted=false`
- `path_generated=false`

只有 gate ready 且本轮只调用 planner-only `ComputePathToPose` 时，才允许 `path_generation_attempted=true`。即使 planner-only attempt 发生，也仍禁止 NavigateToPose、route execution、`/cmd_vel`、`/api/base/manual` 和 WAVE ROVER UART。

## 验收命令

计划阶段验收命令如下：

```bash
git diff --check -- sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|managed_runtime_wait_result|AMCL CLI|ros2 node list|partial_runtime_in_progress|path_generation_attempted=false|path_generated=false|safe_to_control=false|robot-algorithm-engineer" sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout
```

后续 implementation 阶段给 `robot-algorithm-engineer` 的验收命令：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-timeout-s 60 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/artifacts/local_o10_runtime_wait_amcl_cli_closeout.raw.json
```

```bash
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout
```

true-board 运行命令由 Algorithm worker 根据现有 SSH/部署口径执行，但必须保持 no-motion，且最终拉回 live artifact 到本 sprint `artifacts/` 目录。

## Acceptance Criteria

P0 acceptance：

- true-board artifact 出现 final `managed_runtime_wait_result`
- AMCL CLI fallback live closeout 被消费，或 artifact 明确说明为何尚未到达 AMCL CLI fallback 阶段
- 若仍 blocked，root cause 必须比 `23-49` 的 `partial_runtime_in_progress` + `ros2 node list` + `TimeoutExpired` 更窄
- `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false` 保持
- gate 未 ready 时 `path_generation_attempted=false`、`path_generated=false` 保持

P1 acceptance：

- 若 `map_server_active=true`、`amcl_active=true`、`amcl_pose_observed=true`、`map_to_odom_dynamic.observed=true`，允许 planner-only `ComputePathToPose` attempt
- 若 planner-only attempt 发生，必须记录 `path_generation_attempted=true` 与 `path_generated` 结果
- 若 `path_generated=true`，仍只可声明 planner-only path proof，不得声明 route execution、delivery success 或 HIL

## 风险与失败边界

- 最大风险：true-board graph wait 继续卡在 `ros2 node list`，AMCL CLI fallback 无法进入现场 closeout。此时必须把 blocker 收窄到 graph wait，不能把 fallback 已执行重复记为进展。
- 第二风险：AMCL CLI fallback 执行后仍发现 `/tf` 或 `/tf_static` 缺失；这仍是有价值的 root cause，但不允许 path attempt。
- 第三风险：为了追求 `path_generation_attempted=true` 越过 no-motion 或 gate 边界；一旦发生，本轮证据作废。
- 第四风险：本轮只产生 partial artifact。若没有 final `managed_runtime_wait_result`，`final.md` 必须明确 blocked，不能调整 OKR 百分比或归档 KR。
