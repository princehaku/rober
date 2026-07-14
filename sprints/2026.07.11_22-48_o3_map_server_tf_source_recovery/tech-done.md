# O3 Map Server TF Source Recovery Tech Done

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/`
- Owner: `robot-algorithm-engineer`
- Finished at: `2026-07-11 23:10 CST`
- Scope boundary: strict no-motion localization/path readiness proof only. No `/cmd_vel`, no `/api/base/manual`, no NavigateToPose, no WAVE ROVER UART, no O5/O6/O7/UI/cloud changes.

## 自主能力目标和本轮抓手

本轮目标不是重复上轮 `/amcl active [3]`，而是把 `map_server_active=false` 与
`tf_source_probe_not_executed` 从同一团 preflight 失败里拆开。

本轮抓手：

1. 把 board source preflight 拆成 `cli_ready` 与 `runtime_ready`，避免 `rclpy` 抖动把 managed runtime / lifecycle / TF source 一起误判死。
2. 让 TF source probe 在不能跑 rclpy inventory 时也返回明确 boundary，而不是只留下 `tf_source_probe_not_executed`。

## 改动文件和接口影响

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - `board_source_preflight()` 新增 `cli_ready` / `runtime_ready`，把 ROS CLI 与 rclpy runtime 分层。
  - `build_proof()` 改为允许 `cli_ready=true` 时继续进入 managed runtime、lifecycle 和 CLI 只读链路。
  - `collect_tf_source_diagnostics()` 在 CLI 可用但 rclpy runtime 不可用时，返回 `executed=true` 的明确边界 `tf_source_probe_rclpy_runtime_unavailable_after_board_preflight`。
  - `default_tf_source_diagnostics()` 改为保留具体 `root_cause_reason` / `probe_boundary`，不再固定写死 `tf_source_probe_not_executed`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 preflight readiness 分层测试。
  - 新增 TF source probe 在 rclpy runtime 不可用时的 boundary 回归测试。
- `docs/navigation/field_route_evidence_preflight.md`
  - 同步 `cli_ready` / `runtime_ready` 的语义与 TF source 新收口规则。
- `docs/navigation/fixed_route_workflow.md`
  - 同步 fixed-route/no-motion closeout 读取顺序，不再接受泛化 `tf_source_probe_not_executed` 作为最终表述。
- `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/artifacts/`
  - 新增本机 fail-closed artifact。
  - 新增真实板 partial live artifact。

接口影响：只扩展 no-motion proof artifact 的 readiness / boundary 诊断字段，不改变安全合同。`safe_to_control`、`publishes_cmd_vel`、`calls_base_manual`、`robot_control_executed`、`route_execution_success`、`delivery_success`、`hil_pass`、`uses_base_uart` 继续固定 false。

## 实现内容

### 1. 拆开 board source gate

旧逻辑把 `ros2` CLI 与 `rclpy import` 合并成一个 `ready`。结果是：

- 只要板端 `rclpy` import 抖动；
- managed runtime 就直接跳过；
- lifecycle / TF source / path gate 也一起退化成 preflight failure。

现在 helper 明确区分：

- `cli_ready=true`：允许继续做 managed runtime、lifecycle、topic/node/TF 的 CLI 只读路径；
- `runtime_ready=true`：额外表示 rclpy inventory 也可以安全执行。

### 2. TF source probe 不再只剩 “not executed”

旧逻辑里只要前置 gate 不满足，TF source 很容易直接变成 `tf_source_probe_not_executed`。
现在如果 CLI 已恢复，但 rclpy inventory 仍不可跑，artifact 会明确写成：

- `executed=true`
- `boundary=tf_source_probe_rclpy_runtime_unavailable_after_board_preflight`

这样 closeout 至少能分清：

- ROS CLI 根本不可用；
- 还是 CLI 已经恢复，但 rclpy child/inventory 自己不可用。

## 测试、dry-run 或上车验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Exit code: `0`

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- Exit code: `0`
- 关键输出：

```text
Ran 74 tests in 2.239s
OK
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/artifacts/local_o10_map_server_tf_source_recovery.raw.json
```

- Exit code: `2`
- 本机预期 fail-closed：缺 `/opt/ros/humble/setup.bash` 与 `/root/rober/onboard/install/setup.bash`。
- 关键字段：
  - `map_server_active=false`
  - `amcl_active=false`
  - `amcl_pose_observed=false`
  - `tf_readiness_summary.blocked_reason=tf_source_probe_skipped_without_ros2_cli`
  - `path_generation_attempted=false`
  - `path_generated=false`

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3.10 scripts/o10_amcl_nav2_runtime_proof.py ...'
```

- `scp` exit `0`
- 真板 helper 产物已成功落盘，但本次进程未自然结束；保留 partial artifact 后中断 SSH 会话收口。
- 当前 live artifact 为 `partial_runtime_in_progress`，关键字段：
  - `board_source_preflight.classification=board_source_preflight_ready`
  - `board_source_preflight.cli_ready=true`
  - `board_source_preflight.runtime_ready=true`
  - `managed_runtime_started=true`
  - `managed_runtime_wait_result.reason=managed_runtime_wait_timeout`
  - `map_server_active=false`
  - `amcl_active=false`
  - `amcl_pose_observed=false`
  - `tf_readiness_summary.blocked_reason=/tf_topic_missing`
  - `path_generation_attempted=false`
  - `path_generated=false`

这说明本轮确实把 blocker 从“preflight 把整条链一起判死”推进到了：

1. preflight 已 clean ready；
2. managed runtime 真实启动了；
3. 当前更窄 blocker 落在 managed runtime wait graph / lifecycle 未稳定 active，且 `/tf` source 仍未出现。

### artifact invariant check

对 live artifact 跑了本地不变式检查，结果：

- 所有 safety/control/HIL/delivery 字段仍为 `false`
- `path_generation_requested=true`
- `path_generation_attempted=false` 时 `path_generation_gate.blocked_reason` 存在
- 不再使用 `tf_source_probe_not_executed` 作为最终 blocked reason

## 数据、样本或调试输出变化

- `artifacts/local_o10_map_server_tf_source_recovery.raw.json`
  - 本机 fail-closed 样本，证明新的 TF source skipped reason 已从泛化字段下钻到 `ros2_cli_unavailable...`。
- `artifacts/live_o10_map_server_tf_source_recovery.raw.json`
  - 真实板 partial artifact，证明：
    - `board_source_preflight_ready`
    - `managed_runtime_started=true`
    - `managed_runtime_wait_timeout`
    - `rclpy_node_names_failed` 多次 timeout
    - `amcl_param_probe_failed` 命中 `librcl_action.so` / `_rclpy_pybind11` ImportError
    - `tf_readiness_summary.blocked_reason=/tf_topic_missing`

## 失败定位

本轮没有停在旧的 `tf_source_probe_not_executed`，而是继续前移到了两个更具体的真实 blocker：

1. **managed runtime wait graph probe 超时**
   - `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed`
   - 导致 wait 阶段始终没有观测到 `/map_server`、`/amcl` active。
2. **AMCL/TF rclpy inventory 仍有 ROS Python 共享库导入失败**
   - `tf_source_root_cause_detail.amcl_param_probe_error` 命中
     `librcl_action.so` / `_rclpy_pybind11` ImportError
   - 结果 `/tf` source inventory 继续失败，当前收口到 `/tf_topic_missing`。

## 剩余风险和下一步能力建设建议

- 本轮虽然把 preflight 误伤修掉了，但还没有拿到：
  - `map_server_active=true`
  - `amcl_active=true`
  - `amcl_pose_observed=true`
  - `map_to_odom_dynamic.observed=true`
  - `path_generation_attempted=true`
- 真板 helper 本次没有自然退出，当前 live 证据是 partial，不是 final closeout artifact。
- `rclpy_node_names()` 与 `collect_amcl_rclpy_probe()` 在板端仍可能被 Python/ROS shared library 环境拖慢或导入失败。

下一轮最小建议：

1. 继续由 `robot-algorithm-engineer` 单线闭环。
2. 先修 board 侧 managed runtime wait graph probe 的 `rclpy_node_names_failed` timeout。
3. 再把 `collect_amcl_rclpy_probe()` 的 `librcl_action.so` / `_rclpy_pybind11` import failure 收紧到可复验单点。
4. 只有 `map_server_active=true`、`amcl_active=true`、`/tf` source 可见后，才允许继续看 planner-only `ComputePathToPose` attempt。

## live/local artifact 关键字段

### local

- `map_server_active=false`
- `amcl_active=false`
- `amcl_pose_observed=false`
- `tf_readiness_summary.blocked_reason=tf_source_probe_skipped_without_ros2_cli`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

### live

- `map_server_active=false`
- `amcl_active=false`
- `amcl_pose_observed=false`
- `tf_readiness_summary.blocked_reason=/tf_topic_missing`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`
