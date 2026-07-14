# Side2Side Check - O3 Map Server Configure Failure Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Check time: `2026-07-12 14:24 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_configure_failure_repair_only`

## 对照输入

上一轮 accepted artifact：

- `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/live_o10_map_server_transition_callback_probe.raw.json`
- `proof.root_causes[0].reason=map_server_configure_callback_return_failure`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_callback_return_failure`
- `service_rpc_timing.inferred_change_state_response=failure`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`
- `/map_server` not lifecycle-clean/active

本轮 artifact：

- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/live_o10_map_server_configure_failure_repair.raw.json`
- `proof.root_causes[0].reason=map_server_configure_return_failure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_return_failure_before_deferred_map_read_completed`
- `runtime_log_window.events.map_read_after_state_change_failure=true`
- `runtime_log_window.dds_transport_error_text=""`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`
- `/map_server` still not lifecycle-clean/active

## 验收对照

| 维度 | 上轮 | 本轮 | Product 判断 |
| --- | --- | --- | --- |
| root cause | `map_server_configure_callback_return_failure` | `map_server_configure_return_failure_before_deferred_map_read_completed` | 接受为更窄 root cause |
| DDS/SHM | 仅继承旧 runtime env | `RMW_FASTRTPS_USE_SHM=0` 与 `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` 进入 ROS 子进程护栏，live artifact 无 SHM error text | 接受为噪声隔离 |
| map IO ordering | 未拆 before/after | state-change failure 在 deferred map read completed 前被归一 | 接受为下轮可执行方向 |
| lifecycle clean | 未完成 | 未完成 | 不计完成 |
| safety/motion | all false | all false | 符合 strict no-motion |

## 验证核对

来自 `tech-done.md`：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` return `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` return `0` with `Ran 123 tests in 2.272s OK`。
- local strict no-motion dry-run return `2` fail-closed。
- board mkdir/scp return `0`。
- true-board strict no-motion run return `2` with `reason=map_server_configure_return_failure_before_deferred_map_read_completed`。
- artifact pull return `0`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` return `0`，该文件本轮未编辑但 scoped worktree 已 dirty。
- scoped `git diff --check` return `0`。

主节点补充验收：

- live artifact top `root_causes[0].reason` 与 `map_server_transition_callback_probe.canonical_classification` 均为 `map_server_configure_return_failure_before_deferred_map_read_completed`。
- no-motion fields 继续固定 false：`path_generation_attempted`、`path_generated`、`safe_to_control`、`publishes_cmd_vel`、`calls_base_manual`、`robot_control_executed`、`route_execution_success`、`delivery_success`、`hil_pass`、`uses_base_uart`。
- scoped `git diff --check` 无输出。

## Product Acceptance

Accepted as O3/O1 strict no-motion blocker narrowing only。

接受理由：

- 本轮没有修到 `/map_server` lifecycle clean/active，但满足 tech-plan 的 fallback acceptance：比 `map_server_configure_callback_return_failure` 更窄。
- root cause 已进入 configure ChangeState failure 与 deferred map read completion ordering 层。
- DDS SHM 端口锁被显式隔离，不再作为本轮 primary root cause。
- 所有 motion/control/delivery/HIL 字段仍为 false。

不接受为：

- lifecycle clean。
- same-run path generation。
- Nav2 route execution。
- delivery/operator acceptance。
- current live HIL。
- safe-to-control。
- production cloud evidence。

## 下一轮建议

Robot Software 继续主责，直接查 lifecycle manager ChangeState response handling、map_server `on_configure` return path、map IO completion ordering、executor timing 和 bond creation prerequisites。Algorithm 仍等 `/map_server` lifecycle clean 后再接 `/map`、AMCL pose、dynamic `map->odom` 和 planner-only path gate。Hardware 暂不介入，除非后续证据证明 LiDAR serial/runtime/接线事实成为 primary blocker。
