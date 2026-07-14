# Tech Done - O3 Source-Amortized CLI Preflight Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/`
- Implementation owner: `robot-software-engineer`
- Completed at: `2026-07-12 06:10 CST`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_runtime_diagnostic_only`

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `trashbot.o10.source_amortized_cli_preflight.v1` 主路径。
  - `board_source_preflight` 现在通过一次 bounded shell 完成 ROS setup、workspace setup、`cd workdir`、`command -v ros2`、`which ros2`、`type -a ros2`、`ros2 --help` 和 child Python `rclpy import`。
  - 保留 legacy artifact 字段：`source_stage`、`path_lookup`、`cli_invocation`、`python_rclpy`、`ros2_cli_path_ok`、`ros2_cli_invocation_ok`、`ros2_cli_ok`、`cli_ready`、`runtime_ready`、`classification`、`commands`。
  - 新增 amortized shell 事实字段：`source_amortized_cli_preflight_schema`、`source_and_cli_in_one_shell`、`per_command_source_overhead_eliminated`、`commands_executed_after_single_source`、`amortized_shell`。
  - 增加 `--output-json` alias，以及 `--strict-no-motion` / `--no-base-uart` 兼容护栏 flag；这些 flag 不启用任何运动路径。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - targeted tests 改为模拟单 payload source-amortized preflight。
  - 新增 PATH lookup timeout 优先分类、CLI invocation timeout、no-motion CLI alias 和字段兼容覆盖。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录 2026-07-12 起 board source preflight 在同一 amortized shell 中完成 source/path/CLI/rclpy import。
- `docs/navigation/fixed_route_workflow.md`
  - 更新 fixed-route/no-motion closeout 读数顺序和新分类规则。
- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/artifacts/`
  - 新增 local dry-run artifact：`local_source_amortized_cli_preflight_dry_run.raw.json`
  - 新增 true-board live artifact：`live_o10_source_amortized_cli_preflight.raw.json`

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- RC: `0`
- 输出：无错误。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- RC: `0`
- 结果：`Ran 96 tests in 2.251s` / `OK`

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --output-json sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/artifacts/local_source_amortized_cli_preflight_dry_run.raw.json
```

- RC: `2`
- 结果：按预期 fail-closed，并写出 local artifact。
- 失败定位：macOS 本地没有 `/opt/ros/humble/setup.bash` 和 `/root/rober/onboard/install/setup.bash`，`board_source_preflight.classification=board_source_preflight_source_failed`。
- no-motion 字段：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- RC: `0`
- 结果：helper 已推送到 true board。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 240s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --output-json /tmp/live_o10_source_amortized_cli_preflight.raw.json'
```

- RC: `2`
- 结果：true-board run fail-closed，并写出 `/tmp/live_o10_source_amortized_cli_preflight.raw.json`。
- 本轮收窄：`source_stage_ok=true`、`ros2_cli_path_ok=true`、`rclpy_import_ok=true`，但 `ros2_cli_invocation_ok=false`，`cli_ready=false`，`runtime_ready=false`。
- 新 blocker：`board_source_preflight.classification=board_source_preflight_ros2_cli_invocation_timeout`，`cli_invocation.command="ros2 --help >/dev/null"` 在 `6.0s` budget 内 timeout。
- 额外 blocker：canonical map proof 仍为 `map_lifecycle_proof_not_clean`。

```bash
scp -P 37878 root@192.168.1.11:/tmp/live_o10_source_amortized_cli_preflight.raw.json \
  sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/artifacts/live_o10_source_amortized_cli_preflight.raw.json
```

- RC: `0`
- 结果：live artifact 已拉回本 sprint artifacts。

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair
```

- RC: `0`
- 输出：无 whitespace error。

## Artifact 结论

### Local dry-run

- Artifact: `artifacts/local_source_amortized_cli_preflight_dry_run.raw.json`
- `status=blocked_with_root_cause`
- `board_source_preflight.classification=board_source_preflight_source_failed`
- `cli_ready=false`
- `runtime_ready=false`
- `source_and_cli_in_one_shell=true`
- `per_command_source_overhead_eliminated=false`
- no-motion false fields 全部保持 false。

### True-board live

- Artifact: `artifacts/live_o10_source_amortized_cli_preflight.raw.json`
- `status=blocked_with_root_cause`
- `board_source_preflight.source_amortized_cli_preflight_schema=trashbot.o10.source_amortized_cli_preflight.v1`
- `source_and_cli_in_one_shell=true`
- `per_command_source_overhead_eliminated=true`
- `source_stage_ok=true`
- `ros2_cli_path_ok=true`
- `rclpy_import_ok=true`
- `ros2_cli_invocation_ok=false`
- `cli_ready=false`
- `runtime_ready=false`
- `classification=board_source_preflight_ros2_cli_invocation_timeout`
- Root causes:
  - `canonical map proof`: `map_lifecycle_proof_not_clean`
  - `ROS install/source`: `board_source_preflight_ros2_cli_invocation_timeout`
- no-motion false fields 全部保持 false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

## 失败定位

本轮已经把上轮 helper blocker 从 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch` 收窄：

- true-board source 与 workspace setup 成功；
- `command -v ros2`、`type -a ros2`、`which ros2` 都在同一个 sourced shell 中成功；
- child Python `import rclpy` 成功；
- 唯一 CLI readiness blocker 是 `ros2 --help` 在 6 秒 invocation budget 内 timeout。

因此下一轮不应再按 source/path/env mismatch 处理，应直接验证 `ros2 --help` 冷启动预算、CLI plugin discovery、或改用更轻量的 CLI readiness invocation。

## 剩余风险

- 本轮没有进入 `/map_server`、`/amcl_pose`、dynamic `map->odom` 或 planner path gate，因为 `cli_ready=false`。
- `map_lifecycle_proof_not_clean` 仍存在，helper CLI ready 后还需要回到 map lifecycle / AMCL / TF。
- 本轮不证明 path generation、NavigateToPose、route execution、delivery/operator acceptance、HIL pass、safe-to-control 或 production cloud。
- true-board artifact 是 strict no-motion diagnostic，只证明 source/path/rclpy 已穿过，且 CLI invocation timeout 是当前更窄 blocker。

## 协同需求

- Product：无需调整 `OKR.md` 百分比；本轮仍是 O3/O1 supporting no-motion diagnostic delta。
- Hardware：不需要。本轮未打开 WAVE ROVER UART，未改串口/接线/底盘配置。
- Autonomy：暂不需要。等 `cli_ready=true` 后再回到 map lifecycle、AMCL pose、TF 和 planner path gate。
- Full-Stack：不需要。本轮未改 UI/API surface。
