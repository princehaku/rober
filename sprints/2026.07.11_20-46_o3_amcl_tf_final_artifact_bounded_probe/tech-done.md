# O3 AMCL TF Final Artifact Bounded Probe Tech Done

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/`
- Owner: `robot-algorithm-engineer`
- Finished at: `2026-07-11 21:07:43 CST`
- Scope boundary: strict no-motion AMCL/TF/path readiness proof. No `/cmd_vel`, no `/api/base/manual`, no NavigateToPose goal, no WAVE ROVER UART, no cloud/O6/O7/UI changes.

## 自主能力目标和本轮抓手

本轮目标是在 19-46 已修复 `board_source_preflight_ready` 的基础上，不再消费旧 source/CLI blocker，继续把 AMCL lifecycle、`/amcl_pose` sample、dynamic `map->odom`、downstream `map->base_link` 和 planner-only path gate 拆成可验收字段。

本轮抓手是让 `o10_amcl_nav2_runtime_proof.py` 在 final、partial、timeout、SIGTERM 或 SSH 中断时都尽量落盘同形 artifact，并保证 `sigterm_before_final_artifact` 不遮住已经观测到的 AMCL/TF root cause。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `artifact_closeout`，在 final/partial artifact 中记录 `primary_root_cause`、`signal_root_causes`、`last_phase` 和 `current_command`。
  - 新增 `amcl_readiness_summary`，拆分 `/amcl` lifecycle active 与 `/amcl_pose` topic type、publisher/subscriber、sample timing、stamp/freshness 和 blocked reason。
  - 新增 `tf_readiness_summary`，拆分 dynamic `map_to_odom`、`odom_to_base_link` 和 downstream derived `map_to_base_link`。
  - 新增 `path_generation_gate`，记录 requested/attempted/generated、point count、planner readiness 和 not-attempted root cause。
  - managed runtime wait 和 early `/amcl_pose` probe 会写入 phase snapshot，使 TF 阶段中断时 partial artifact 也保留 AMCL lifecycle/sample 摘要。
  - `main()` 未预期异常时会尽量写 `exception_before_final_artifact` partial，而不是只返回 nonzero。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 partial closeout、AMCL lifecycle/sample split、TF edge split、path generation not attempted gate 和 no-motion false 字段回归测试。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录 20:46 新增 artifact 字段、live 结论和 no-motion proof boundary。
- `docs/navigation/fixed_route_workflow.md`
  - 同步 fixed-route/no-motion 读取顺序：`board_source_preflight -> amcl_readiness_summary -> tf_readiness_summary -> path_generation_gate`。
- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/`
  - 新增 local fail-closed artifact。
  - 新增 live artifact。

接口影响：只向 `proof` artifact 追加可读摘要字段；CLI 参数保持兼容。所有 control/HIL/delivery 字段保持 false。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Exit code: `0`
- 关键输出：无输出，语法检查通过。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- Exit code: `0`
- 关键输出：

```text
Ran 69 tests in 2.210s
OK
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py ... --output sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/local_o10_amcl_tf_final_artifact_bounded_probe.raw.json
```

- Exit code: `2`
- 预期本机 fail-closed：macOS 本机没有 `/opt/ros/humble/setup.bash` 和 `/root/rober/onboard/install/setup.bash`。
- artifact 关键字段：
  - `status=blocked_with_root_cause`
  - `board_source_preflight.classification=board_source_preflight_source_failed`
  - `path_generation_requested=true`
  - `path_generation_attempted=false`
  - `path_generated=false`
  - `artifact_closeout.primary_root_cause.reason=map_lifecycle_latest_missing`
  - `safe_to_control=false`

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Exit code: `0`
- 运行两次；第二次为修正 partial 摘要后的最终 helper 版本。

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py ... --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

- Exit code: `255`
- 说明：live SSH 会话两次都没有在 helper/managed runtime 预算附近自然返回，均由本地 `Ctrl-C` 中断。
- 影响：命令 exit code 不能当作 helper 自然收口成功；必须以拉回的 `/root/rober/onboard/runtime/nav2_lifecycle_latest.json` 为准。
- 第二次中断后拉回的 artifact 已是 final `blocked_with_root_cause`，不是 partial，说明 helper 后续仍完成了 final 写出和 cleanup。

```bash
ssh -p 37878 root@192.168.1.11 'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' > sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/live_o10_amcl_tf_final_artifact_bounded_probe.raw.json
```

- Exit code: `0`
- live artifact 已拉回本 sprint artifacts。

```bash
python3 - <<'PY'
...
print("artifact_invariants_ok")
PY
```

- Exit code: `0`
- 关键输出：`artifact_invariants_ok`

## Live Artifact 结论

`live_o10_amcl_tf_final_artifact_bounded_probe.raw.json` 结论：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `board_source_preflight.classification=board_source_preflight_ready`
- `ros2_cli_ok=true`
- `rclpy_import_ok=true`
- `managed_runtime_started=true`
- `amcl_readiness_summary.ready=false`
  - `/amcl` lifecycle readback 为 `inactive [2]`
  - `/amcl_pose.topic_type=geometry_msgs/msg/PoseWithCovarianceStamped`
  - `/amcl_pose` sample observed，但 stamp stale，`age_ms=85437`
- `tf_readiness_summary.ready=false`
  - `map_to_odom_dynamic.observed=false`
  - `map_to_base_link.observed=false`
  - `map_to_base_link.blocking_segment=map_to_odom`
- `path_generation_requested=true`
- `path_generation_attempted=false`
- `path_generated=false`
- `path_generation_gate.blocked_reason=path_generation_blocked_by_localization_not_ready`
- `planner_server_ready_for_path_generation=true`，但 localization/TF gate 未 ready，故没有调用 ComputePathToPose。

Root causes:

- `map_lifecycle_proof_not_clean`
- `map_server_lifecycle_not_active_during_preflight`
- `amcl_lifecycle_not_active_during_preflight`
- `map_server_lifecycle_not_active`
- `amcl_lifecycle_not_active`
- `/scan_reliable_and_best_effort_timeout`
- `/map_once_not_observed`
- `cli_initialpose_publish_failed`
- `map_to_odom_dynamic_source_missing`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `localization_not_ready_for_path_generation`

Safety/no-motion invariants:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## 失败定位

本轮不再 blocked 在旧 `ros2_cli_ok=false`、`rclpy_import_ok=false` 或 source/CLI blocker。真实板 source、ROS2 CLI 和 rclpy 均 ready。

新的最小定位是 localization gate 未 ready：

1. managed runtime 启动了；
2. `/amcl_pose` 有样本但 stale；
3. `/amcl` lifecycle 为 inactive；
4. `/scan` BEST_EFFORT / RELIABLE 双 QoS 仍 timeout；
5. `/map` once 未观测；
6. dynamic `map->odom` 未出现，因此 downstream `map->base_link` 被阻塞；
7. path generation 只 requested，未 attempted，保持 `path_generated=false`。

因此本轮是 AMCL/TF/path gate bounded final artifact 收敛，不是 path generation success、route execution、HIL 或 delivery。

## 数据、样本或调试输出变化

- local artifact: `artifacts/local_o10_amcl_tf_final_artifact_bounded_probe.raw.json`
- live artifact: `artifacts/live_o10_amcl_tf_final_artifact_bounded_probe.raw.json`
- live artifact 现在可直接消费：
  - `artifact_closeout`
  - `amcl_readiness_summary`
  - `tf_readiness_summary`
  - `path_generation_gate`

## 剩余风险和下一步

- live SSH command 仍需要人工中断，虽然 helper 写出了 final artifact；下一轮应继续收敛远端命令自然返回边界。
- `/amcl` inactive、`/scan` 双 QoS timeout、`/map_once_not_observed`、`cli_initialpose_publish_failed` 和 dynamic `map->odom` 缺失仍未解除。
- path generation 没有 attempt；不能提升 OKR 百分比，不能交给 O6/O7 作为 route execution 或 delivery material。
- 下一轮最小命令仍是同一 no-motion helper，优先修 `/amcl` lifecycle active 与 dynamic `map->odom`，再让 planner-only `ComputePathToPose` 进入 attempted/generated。
