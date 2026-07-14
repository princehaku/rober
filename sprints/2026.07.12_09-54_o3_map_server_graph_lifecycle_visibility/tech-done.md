# tech-done

- sprint_type: epic
- owner: Robot Software Engineer
- scope: O3 strict no-motion `/map_server` graph/lifecycle visibility
- date: 2026-07-12

## 实际改动

本轮扩展 `onboard/scripts/o10_amcl_nav2_runtime_proof.py`，新增
`proof.map_server_graph_lifecycle_visibility` 结构化摘要，schema 为
`trashbot.o10.map_server_graph_lifecycle_visibility.v1`。该摘要把 `/map_server`
graph inventory、daemon/DDS visibility、lifecycle first/retry readback、timeout
budget、elapsed、stdout、stderr、returncode、managed runtime/process startup context
和 canonical classification 汇总到同一个字段，供 O3 gate 直接读取。

新增 canonical classification 覆盖：

- `map_server_node_absent`
- `lifecycle_manager_or_process_startup_missing`
- `daemon_or_dds_graph_visibility_failed`
- `helper_budget_or_timing_exhausted`
- `map_server_lifecycle_active`

同时补了 `path_generation_envelope_fields()`，让最终 artifact 顶层也显式输出
`path_generation_attempted=false` 与 `path_generated=false`，避免 strict no-motion
消费端读到 `null`。该字段只镜像 `proof` 内实际状态，不改变 path generation opt-in
路径。

测试文件 `onboard/tests/test_nav2_runtime_proof_helper.py` 新增 targeted unittest，覆盖
node absence、graph visible lifecycle timeout、daemon/DDS graph visibility failure、
helper budget/timing exhausted、lifecycle manager/process startup missing、active case、
安全字段 false，以及 partial artifact 顶层 path generation 字段。

文档同步更新：

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

两份文档补充 09-54 proof boundary、`/map_server` graph/lifecycle visibility 读法、
与 08-55/07-53 的区别，以及 no-motion 红线。

## Artifact

本轮生成 artifact：

- local dry-run: `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts/local_o10_map_server_graph_lifecycle_visibility.raw.json`
- live board: `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts/live_o10_map_server_graph_lifecycle_visibility.raw.json`

live board 关键字段：

```json
{
  "status": "blocked_with_root_cause",
  "board_source_preflight": "board_source_preflight_ready",
  "lightweight_cli_ready": true,
  "cli_ready": true,
  "runtime_ready": true,
  "amcl_active": true,
  "map_server_active": false,
  "canonical_classification": "map_server_node_absent",
  "failure_detail": "lifecycle_retry_node_not_found",
  "amcl_live_state_regression": false,
  "first_attempt": {
    "timed_out": true,
    "timeout_s": 10.0,
    "elapsed_ms": 10067,
    "returncode": null
  },
  "retry_attempt": {
    "timed_out": false,
    "timeout_s": 18.0,
    "elapsed_ms": 12933,
    "returncode": 1,
    "stderr": "Node not found\n"
  },
  "path_generation_attempted": false,
  "path_generated": false
}
```

解释：08-55 true-board artifact 中 `/map_server` retry `Node not found` 现在被明确归类为
`map_server_node_absent`。daemon/DDS graph timeout 仍保留为 guarded context，但不覆盖
`Node not found` 这个更具体的 lifecycle readback 结论。`/amcl active [3]` 保留，
`amcl_live_state_regression=false`。

local dry-run 关键字段：

```json
{
  "status": "blocked_with_root_cause",
  "board_source_preflight": "board_source_preflight_source_failed",
  "lightweight_cli_ready": false,
  "cli_ready": false,
  "runtime_ready": false,
  "canonical_classification": "lifecycle_manager_or_process_startup_missing",
  "failure_detail": "map_server_not_visible_without_daemon_timeout",
  "path_generation_attempted": false,
  "path_generated": false
}
```

local 失败定位：macOS 本机缺 `/opt/ros/humble/setup.bash` 和 ROS2 runtime，因此按预期
fail-closed；该结果只证明本地无 ROS2 环境下安全字段保持 false，不作为 board 运行结论。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，exit code 0。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：通过，`Ran 110 tests in 2.255s`，`OK`。

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --output-json sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts/local_o10_map_server_graph_lifecycle_visibility.raw.json
```

结果：exit code 2，预期 fail-closed。根因是本机 ROS2 source 失败：
`board_source_preflight_source_failed`。危险字段均为 false。

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

结果：通过，exit code 0。

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，exit code 0。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --output-json /tmp/rober_o10_artifacts/live_o10_map_server_graph_lifecycle_visibility.raw.json'
```

结果：exit code 2，按 helper 语义表示 blocked artifact 已写出。关键结论：
`board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、
`runtime_ready=true` 不回退；`/amcl active [3]` 保留；`/map_server` classified as
`map_server_node_absent`，retry `stderr="Node not found\n"`。

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_graph_lifecycle_visibility.raw.json \
  sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts/live_o10_map_server_graph_lifecycle_visibility.raw.json
```

结果：通过，exit code 0。

## No-motion 安全边界

本轮没有发送 NavigateToPose，没有发布 `/cmd_vel`，没有调用 `/api/base/manual`，没有打开
WAVE ROVER UART。local 与 live artifact 中以下字段均为 false：

- `safe_to_control`
- `publishes_cmd_vel`
- `calls_base_manual`
- `robot_control_executed`
- `route_execution_success`
- `delivery_success`
- `hil_pass`
- `uses_base_uart`
- `path_generation_attempted`
- `path_generated`

downstream `/scan`、`/map`、TF 只作为 guarded context 记录；本轮 primary 证据仅为
`/map_server` graph/lifecycle visibility。

## 剩余风险

`/map_server` 仍未 active，且 retry 明确返回 `Node not found`，因此不能进入 path generation、
route execution、delivery 或 HIL 结论。live stdout 中仍可见 `RTPS_TRANSPORT_SHM` port lock
warning，当前只作为 lifecycle CLI 输出噪声记录，未证明其是主因。

需要协同：

- Product：验收 09-54 proof boundary 和 OKR 计分是否仍保持 O3 no-motion support-only。
- Algorithm：等 `/map_server` lifecycle clean 后，再继续 `/map`、TF、localization/path gate。
- Hardware：本轮不需要；未触碰 WAVE ROVER、UART、串口或硬件配置。
- Full-Stack：本轮不需要；未触碰 O7 UI/API surface。
