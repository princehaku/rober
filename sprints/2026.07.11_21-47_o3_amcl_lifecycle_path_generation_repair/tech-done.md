# O3 AMCL Lifecycle Path Generation Repair Tech Done

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/`
- Owner: `robot-algorithm-engineer`
- Finished at: `2026-07-11 22:17:00 CST`
- Scope boundary: strict no-motion localization/path readiness proof only. No `/cmd_vel`, no `/api/base/manual`, no NavigateToPose, no WAVE ROVER UART, no O5/O6/O7/UI/cloud changes.

## 自主能力目标和本轮抓手

本轮目标不是重复 20-46 的 root cause 复述，而是继续把 localization/path gate 往前推一层：优先让 `/amcl` lifecycle 是否 clean active 变成可复验事实，并把 managed runtime wait、`/amcl_pose`、TF 和 path gate 的阻塞边界拆得更窄。

本轮抓手有两个：

1. 修 helper 的 managed runtime wait 语义，让它不再把“节点进 graph”和“lifecycle 真 active”混成一个状态。
2. 修 wait graph probe 的 ROS Python 环境依赖，让 wait 阶段不再因为主进程没继承好 `rclpy` 而假超时。

## 改动文件和接口影响

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - `wait_for_managed_runtime()` 现在在 managed wait 窗口内持续复查 lifecycle，并把 `lifecycle_active`、`lifecycle_results`、`lifecycle_history` 写回 `managed_runtime_wait_result`。
  - `rclpy_node_names()` 改成 sourced child Python probe，不再依赖 helper 主进程自己的 `rclpy` 环境。
  - managed wait 的 node graph probe 外层 timeout 放宽到 `max(timeout_s + 4.5, 6.0)`，避免 source + child 启动本身把 graph probe 卡成假 timeout。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 managed wait lifecycle recheck、nodes-observed-but-inactive、sourced child node graph probe 回归测试。
- `docs/navigation/field_route_evidence_preflight.md`
  - 同步 `managed_runtime_lifecycle_active_observed` / `managed_runtime_nodes_observed_but_lifecycle_inactive` / `managed_runtime_wait_timeout` 三类边界，以及 sourced child node graph probe 修复。
- `docs/navigation/fixed_route_workflow.md`
  - 同步 fixed-route/no-motion 读取顺序，强调先看 `managed_runtime_wait_result`，再看 AMCL/TF/path gate。
- `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/artifacts/`
  - 新增本机 fail-closed artifact。
  - 新增 live partial artifact（修复前中间态）和最终 live artifact（修复后 closeout）。

接口影响：只扩展 proof artifact 的 wait/lifecycle/readiness 诊断字段，不改变 no-motion 合同。所有 `safe_to_control` / `publishes_cmd_vel` / `calls_base_manual` / `robot_control_executed` / `route_execution_success` / `delivery_success` / `hil_pass` / `uses_base_uart` 继续保持 false。

## 实现内容

### 1. managed wait 不再只看 node name

旧逻辑的问题是：

- `wait_for_managed_runtime()` 只要在 graph 里看到 `/map_server`、`/amcl` 节点名，就把 wait 判成成功；
- 之后再用一次性的 `ros2 lifecycle get` 快照补 lifecycle；
- 这样会把“启动中的 inactive”与“真正 active”混成同一种 blocker。

现在 wait 阶段会：

- 先用 sourced child Python probe 看 node graph；
- 只有节点确实进入 graph 后，才开始做 lifecycle recheck；
- 如果 lifecycle 在窗口内到达 active，边界收口到 `managed_runtime_lifecycle_active_observed`；
- 如果节点出现过但 lifecycle 一直没 active，收口到 `managed_runtime_nodes_observed_but_lifecycle_inactive`；
- 如果连节点都没稳定看见，才保留 `managed_runtime_wait_timeout`。

### 2. 修掉 wait graph probe 的假超时来源

修复前 live partial artifact 已经证明，旧 `rclpy_node_names()` 的直接根因不是“runtime 一定没起来”，而是 wait probe 本身跑在 helper 主进程里，重复命中：

- `ModuleNotFoundError: No module named 'rclpy'`
- 后续又出现 `NotInitializedException`

这和后面 sourced child `/scan`/`/amcl_pose` probe 能继续跑通是矛盾的，说明 wait probe 自己有环境漂移。现在 node graph probe 改成和其它 sourced child probe 一样的 sourced child Python 路径，避免主进程环境把 wait 误报成 runtime timeout。

## 测试、dry-run 或上车验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Exit code: `0`

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- 首轮新增测试夹具次数不足，`StopIteration`，已修复。
- 最终 Exit code: `0`
- 关键输出：

```text
Ran 72 tests in 2.225s
OK
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/artifacts/local_o10_amcl_lifecycle_path_generation_repair.raw.json
```

- Exit code: `2`
- 预期 fail-closed：本机缺 `/opt/ros/humble/setup.bash` 与 `/root/rober/onboard/install/setup.bash`。
- 关键字段：
  - `status=blocked_with_root_cause`
  - `board_source_preflight.classification=board_source_preflight_source_failed`
  - `path_generation_requested=true`
  - `path_generation_attempted=false`
  - `path_generated=false`

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Exit code: `0`
- 共执行多次，最终一次为 sourced child node graph probe 修复版。

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py ...'
```

- 多次 live 复验结果如下：

1. 修复前 live partial：
   - artifact: `artifacts/live_o10_amcl_lifecycle_path_generation_repair_attempt1_partial.raw.json`
   - `board_source_preflight_ready`
   - `managed_runtime_wait_result.reason=managed_runtime_wait_timeout`
   - `/amcl_pose` 已 observed 且 stale
   - `map_to_odom` / `map_to_base_link` 仍未 ready
   - 说明旧 wait 超时并不等于 AMCL 根本没起来。

2. 修复 wait graph probe 后的最终 live artifact：
   - artifact: `artifacts/live_o10_amcl_lifecycle_path_generation_repair.raw.json`
   - `status=blocked_with_root_cause`
   - `evidence_type=blocked_with_root_cause`
   - `/amcl` lifecycle 已到 `active [3]`
   - `map_server_active=false`
   - `/amcl_pose` 本轮未 fresh observed
   - `map_to_odom=false`
   - `odom_to_base_link=false`
   - `base_link_to_laser_frame=true`
   - `path_generation_requested=true`
   - `path_generation_attempted=false`
   - `path_generated=false`

这说明本轮至少推进了一层关键 gate：`/amcl` lifecycle active 已从“未证实/经常 inactive”推进为真实板 `active [3]` 事实。

```bash
python3 - <<'PY'
...
print('artifact_invariants_ok')
PY
```

- Exit code: `0`
- 输出：`artifact_invariants_ok`

## 数据、样本或调试输出变化

- `artifacts/local_o10_amcl_lifecycle_path_generation_repair.raw.json`
  - 本机 fail-closed 样本。
- `artifacts/live_o10_amcl_lifecycle_path_generation_repair_attempt1_partial.raw.json`
  - 修复前 live partial，中间态证明 old wait timeout 与 downstream AMCL observation 并不一致。
- `artifacts/live_o10_amcl_lifecycle_path_generation_repair.raw.json`
  - 当前最终 live artifact。

当前 live artifact 的关键新增事实：

- `amcl_readiness_summary.amcl_lifecycle.active=true`
- `amcl_readiness_summary.amcl_lifecycle.result.stdout="active [3]\n"`
- `map_server_active=false`
- `tf_readiness_summary.map_to_odom_dynamic.observed=false`
- `tf_readiness_summary.odom_to_base_link.observed=false`
- `tf_readiness_summary.map_to_base_link.observed=false`
- `path_generation_gate.requested=true`
- `path_generation_gate.attempted=false`
- `path_generation_gate.generated=false`
- `path_generation_gate.blocked_reason=path_generation_blocked_by_localization_not_ready`

## 失败定位

本轮出现过三类失败，均已继续定位而不是直接收口：

1. **新增单测夹具错误**
   - 首轮 `StopIteration`
   - 已修复 mock side effect 次数并复验通过。

2. **旧 wait graph probe 误报**
   - live partial 显示 `managed_runtime_wait_timeout`
   - 但同一轮 `/amcl_pose` 已 observed
   - 继续深挖后确认旧 `rclpy_node_names()` 自己在 wait 阶段误报 `No module named 'rclpy'` / `NotInitializedException`
   - 已改成 sourced child Python probe。

3. **当前剩余真实 blocker**
   - `/amcl` 已 active，但 `map_server` 仍未 active
   - `board_source_preflight.rclpy_import` 仍偶发 timeout
   - `tf_source_probe_not_executed`
   - `map_to_odom` / `odom_to_base_link` 仍未 ready
   - 因 localization/TF gate 未 ready，planner-only path 仍不能 attempt

## 剩余风险和下一步能力建设建议

- 当前 live artifact 证明 `/amcl` active 已达成，但还不是完整 localization gate：
  - `map_server_active=false`
  - `/amcl_pose` 未 fresh observed
  - `map_to_odom=false`
  - `odom_to_base_link=false`
  - `map_to_base_link=false`
- `board_source_preflight_rclpy_import_timeout` 仍偶发；虽然它不再是唯一 first blocker，但会污染同轮 closeout 稳定性。
- `tf_source_probe_not_executed` 说明 TF source inventory 仍没真正跑出来，当前 TF 结论仍主要来自 tf2_echo 和 fail-closed 边界。

下一轮最小建议：

1. 继续由 `robot-algorithm-engineer` 单线闭环。
2. 优先把 `map_server_active` 与 `tf_source_probe_not_executed` 分开修掉。
3. 在 `/amcl` 已 active 的前提下，先恢复 `/amcl_pose` fresh sample 和 dynamic `map->odom`，再看 `ComputePathToPose` attempt。
4. 保持 no-motion，不发布 `/cmd_vel`、不调用 `/api/base/manual`、不发送 NavigateToPose、不打开 WAVE ROVER UART。

## Mission artifact delta / OKR 判断

- **新的 mission artifact delta：有，但仍是 no-motion supporting delta，不是 mission completion delta。**
- 本轮新增的同轮事实是：
  - `/amcl` lifecycle `active [3]`
  - `base_link -> laser_frame` TF 已 observed
  - `path_generation_requested=true` 但仍 `attempted=false` / `generated=false`
- 仍**没有**：
  - fresh `/amcl_pose`
  - dynamic `map->odom`
  - `map->base_link`
  - planner-only path attempt/generated
  - route execution / delivery / HIL / production external evidence

因此：

- O3/O1 supporting artifact 有新增；
- mission / OKR 百分比**应保持不变**；
- 不能把本轮记成 route execution、delivery、HIL 或 production evidence 前进。
