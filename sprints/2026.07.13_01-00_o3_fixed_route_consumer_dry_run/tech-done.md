# Tech Done - O3 Fixed Route Consumer Dry Run

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/`
- Owner: `robot-algorithm-engineer`
- Boundary: strict no-motion fixed-route consumer dry-run material validation.

## 自主能力目标和本轮抓手

本轮抓手是消费 00:00 route-intent packet，让 fixed-route consumer 能在不触发任何运动的前提下读取 `route_intent_summary.json`、`route_intent_replay.jsonl` 和 `route.csv`，并明确这份材料是否足以进入后续 route execution sprint。

本轮只做 artifact-only dry-run/material validation，没有发布 `/cmd_vel`，没有调用 `/api/base/manual`，没有运行 NavigateToPose/controller/BT execution，没有打开 WAVE ROVER UART，也没有改硬件配置。

## 实际改动文件

- `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm/fixed_route_consumer_dry_run_summary.json`
- `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm/fixed_route_consumer_dry_run_events.jsonl`
- `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm/fixed_route_consumer_dry_run_route_check.csv`
- `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/tech-done.md`

未改动 `docs/navigation/fixed_route_workflow.md`、`onboard/scripts/o10_amcl_nav2_runtime_proof.py` 或 `onboard/tests/test_nav2_runtime_proof_helper.py`。本轮没有改变 consumer workflow contract，也没有需要导出的 full structured path helper 改动。

## 实现内容和接口影响

`fixed_route_consumer_dry_run_summary.json` 使用 `trashbot.fixed_route_consumer_dry_run.v1` schema，固定：

- `route_intent_id=route_intent_20260713_0000_from_20260712_2157_path_proof`
- `task_id=task_o3_fixed_route_intent_20260713_0000`
- `validation_status=pass_with_material_boundary`
- `dry_run_status=accepted_partial_material_dry_run`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

consumer dry-run 校验通过的内容：

- summary / JSONL / CSV 的 `route_intent_id` 和 `task_id` 一致。
- source proof ref 与 `source_path_proof_sha256` 保留。
- source evidence 保留 `path_generation_attempted=true`、`path_generated=true`、`path_point_count=21`、`fallback_mode=ros2_cli_action_send_goal`。
- JSONL 为 17 行，包含 metadata、request start anchor、14 个 stdout-tail pose、request goal anchor。
- CSV 为 16 条 material rows，`materialized_order=0..15` 连续，frame/position/quaternion 字段完整。
- strict no-motion invariants 通过，所有控制、路线执行、delivery、HIL 字段保持 false。

consumer dry-run 同时 fail-closed 记录了 `full_structured_path_poses_missing`：源 artifact 没有持久化 full structured path poses，只能验证 partial stdout-tail material，不能声明 full 21-point replay。

接口影响：只新增 sprint 离线 artifact 和 sprint 留档，没有改 ROS2 runtime、launch、hardware config、API、UI、OKR 或 process log。

## 数据、样本和调试输出变化

- `fixed_route_consumer_dry_run_summary.json`：178 行，汇总身份、source evidence、material shape、checks、next evidence。
- `fixed_route_consumer_dry_run_events.jsonl`：29 行，包含 dry-run start、10 个 consumer checks、16 个 route row checks、dry-run completed。
- `fixed_route_consumer_dry_run_route_check.csv`：17 行，含 header 和 16 条 material row 校验结果。

关键结果：

- `materialized_stdout_tail_pose_event_count=14`
- `csv_material_row_count=16`
- `authoritative_path_point_count=21`
- `minimum_unmaterialized_path_pose_count=7`
- `path_pose_materialization_status=partial_stdout_tail_only`
- `full_structured_path_poses_available=false`
- `blocked_reason=full_structured_path_poses_missing`

## 验证结果

JSON 格式化：

```bash
python3 -m json.tool sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm/fixed_route_consumer_dry_run_summary.json >/tmp/fixed_route_consumer_dry_run_summary.pretty.json
```

结果：通过，无输出。

结构断言：

```bash
python3 - <<'PY'
import csv, json
from pathlib import Path
base = Path('sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm')
summary = json.loads((base / 'fixed_route_consumer_dry_run_summary.json').read_text())
assert summary['route_intent_id'] == 'route_intent_20260713_0000_from_20260712_2157_path_proof'
assert summary['task_id'] == 'task_o3_fixed_route_intent_20260713_0000'
assert summary['strict_no_motion'] is True
assert summary['route_execution_success'] is False
assert summary['delivery_success'] is False
assert summary['hil_pass'] is False
events = [json.loads(line) for line in (base / 'fixed_route_consumer_dry_run_events.jsonl').read_text().splitlines()]
assert events
with (base / 'fixed_route_consumer_dry_run_route_check.csv').open(newline='') as f:
    rows = list(csv.DictReader(f))
assert rows
print('fixed_route_consumer_dry_run_ok')
PY
```

结果：

```text
fixed_route_consumer_dry_run_ok
```

Anchor inspection：

```bash
rg -n "route_intent_20260713_0000|task_o3_fixed_route_intent_20260713_0000|strict no-motion|fixed-route consumer dry-run|route_execution_success=false|delivery_success=false|hil_pass=false|full_structured_path_poses_missing|next_evidence_required" \
  sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run
```

结果片段：

```text
artifacts/algorithm/fixed_route_consumer_dry_run_summary.json:150:    "strict no-motion",
artifacts/algorithm/fixed_route_consumer_dry_run_summary.json:151:    "fixed-route consumer dry-run",
artifacts/algorithm/fixed_route_consumer_dry_run_summary.json:152:    "route_execution_success=false",
artifacts/algorithm/fixed_route_consumer_dry_run_summary.json:153:    "delivery_success=false",
artifacts/algorithm/fixed_route_consumer_dry_run_summary.json:154:    "hil_pass=false",
artifacts/algorithm/fixed_route_consumer_dry_run_summary.json:155:    "full_structured_path_poses_missing",
artifacts/algorithm/fixed_route_consumer_dry_run_summary.json:156:    "next_evidence_required"
```

Scoped diff check：

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run
```

结果：通过，无输出。

本轮未改 helper/tests，因此没有运行 optional `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` 或 `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`。

## 失败定位

没有验收命令失败。

材料边界仍是预期 blocker：`full_structured_path_poses_missing`。00:00 packet 可被 fixed-route consumer dry-run 读取和校验，但只包含 14 个 stdout-tail pose，加 request start/goal anchor；它不能证明 full 21-point replay。

## 剩余风险和下一步建议

- 本轮是 strict no-motion fixed-route consumer dry-run material validation，不是 route execution。
- `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false` 保持不变。
- 下一步若要 exact 21-point fixed route，需要让 helper 输出 full structured path poses，或重新采集/导出路线材料。
- 进入路线执行、delivery/operator acceptance、current live HIL 或 production credit 前，必须另起 sprint 产出对应 live evidence。
