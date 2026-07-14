# Tech Done - O3 Fixed Route Intent Replay Material

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/`
- Owner: `robot-algorithm-engineer`
- Boundary: strict no-motion artifact-only route-intent material.

## 自主能力目标和本轮抓手

本轮抓手是把 `2026.07.12_21-57` accepted same-run planner-only path proof 转成 fixed-route / route-intent material，供下一轮 replay、route execution、delivery/operator acceptance、HIL 或 production readback 继续围绕同一个 `route_intent_id` 推进。

本轮只读取本地 source artifact 并做本地解析/校验，没有运行 NavigateToPose，没有发布 `/cmd_vel`，没有调用 `/api/base/manual`，没有打开 WAVE ROVER UART 或硬件设备。

## 实际改动文件

- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route_intent_summary.json`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route_intent_replay.jsonl`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route.csv`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/tech-done.md`

未改动 helper 或测试代码：`onboard/scripts/o10_amcl_nav2_runtime_proof.py`、`onboard/tests/test_nav2_runtime_proof_helper.py` 均未触碰。

## 实现内容和接口影响

生成 `route_intent_id=route_intent_20260713_0000_from_20260712_2157_path_proof` 和 `task_id=task_o3_fixed_route_intent_20260713_0000`，并在 summary、JSONL、CSV 三处保持一致。

`route_intent_summary.json` 消费并引用 source artifact：

- `source_path_proof_ref=sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json`
- `source_path_proof_sha256=39536d8fa0f51cf1d5b9d4eb1c78fd9228aa977ddbb177ed11bd4285efc039bd`
- `path_generated=true`
- `path_point_count=21`
- `fallback_mode=ros2_cli_action_send_goal`

source artifact 的 structured `path_preview_points` 为空，但 CLI fallback `stdout_tail` 可解析出 14 个完整 pose blocks。因此本轮明确标注：

- `path_pose_materialization_status=partial_stdout_tail_only`
- `authoritative_path_point_count=21`
- `materialized_stdout_tail_pose_count=14`
- `minimum_unmaterialized_path_pose_count=7`
- `source_index_status=unknown_due_to_stdout_tail_truncation`

`route_intent_replay.jsonl` 写入 17 行：1 行 metadata、1 行 request start anchor、14 行 stdout-tail pose、1 行 request goal anchor。`route.csv` 写入 16 行 route material：request start anchor、14 行 stdout-tail pose、request goal anchor。start/goal anchor 来自 `path_goal_request`，不是补造缺失 path point。

`docs/navigation/fixed_route_workflow.md` 增加 `2026-07-13 00:00` 小节，说明 planner-only path proof 转 route-intent material 的边界：partial stdout-tail 只能按 partial 标注，不得补造缺失点；route material 仍不能声明 route execution、delivery、HIL 或 safe-to-control。

接口影响：只新增离线 artifact，没有改 ROS2 runtime、launch、hardware config、API、UI、OKR 或 process log。

## 验证结果

Artifact key inspection:

```bash
rg -n "route_intent_id|task_id|source_path_proof_ref|path_generated=true|path_point_count=21|fallback_mode=ros2_cli_action_send_goal|route_execution_success=false|delivery_success=false|hil_pass=false|strict no-motion|next_evidence_required" \
  sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material
```

结果片段：

```text
artifacts/algorithm/route_intent_summary.json:153:    "path_generated=true",
artifacts/algorithm/route_intent_summary.json:154:    "path_point_count=21",
artifacts/algorithm/route_intent_summary.json:155:    "fallback_mode=ros2_cli_action_send_goal",
artifacts/algorithm/route_intent_summary.json:156:    "route_execution_success=false",
artifacts/algorithm/route_intent_summary.json:157:    "delivery_success=false",
artifacts/algorithm/route_intent_summary.json:158:    "hil_pass=false",
artifacts/algorithm/route_intent_summary.json:159:    "strict no-motion",
artifacts/algorithm/route_intent_summary.json:160:    "next_evidence_required"
```

Structured artifact validation:

```bash
python3 -m json.tool sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route_intent_summary.json >/tmp/route_intent_summary.pretty.json && echo summary_json_ok
```

```text
summary_json_ok
```

JSONL / CSV line and header check:

```bash
python3 - <<'PY'
import csv,json
from pathlib import Path
jsonl=Path('sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route_intent_replay.jsonl')
rows=[json.loads(line) for line in jsonl.read_text().splitlines()]
pose_count=sum(1 for r in rows if r.get('event_type')=='route_intent_pose')
assert rows[0]['path_point_count']==21
assert pose_count==14
assert rows[0]['route_execution_success'] is False
print(f'jsonl_ok lines={len(rows)} materialized_pose_events={pose_count}')
csv_path=Path('sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route.csv')
with csv_path.open(newline='') as f:
    reader=csv.DictReader(f)
    csv_rows=list(reader)
assert reader.fieldnames and 'route_intent_id' in reader.fieldnames
assert len(csv_rows)==16
assert csv_rows[0]['source_role']=='request_start'
assert csv_rows[-1]['source_role']=='request_goal'
print(f'csv_ok rows={len(csv_rows)} header_fields={len(reader.fieldnames)}')
PY
```

```text
jsonl_ok lines=17 materialized_pose_events=14
csv_ok rows=16 header_fields=19
```

Scoped diff check:

```bash
git diff --check -- docs/navigation/fixed_route_workflow.md sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material
```

```text
# no output
```

Python helper/tests were not touched, so `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` and `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` were not required for this artifact-only path.

## 失败定位

没有验证失败。

Source extraction limitation is expected and recorded: source artifact reports `path_point_count=21`, but structured `path_preview_points=[]`; only the CLI fallback `stdout_tail` exposed 14 complete pose blocks. 本轮未补造其余 7 个 path poses，已在 artifact 中标注 `partial_stdout_tail_only`。

## 剩余风险和下一步建议

- 本轮是 route-intent material，不是 route execution；`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false` 保持不变。
- 如果下一轮需要 exact 21-point fixed route，必须让 helper 输出 full structured path poses，或重新做 no-motion route capture/replay material。
- 下一步建议先用同一 `route_intent_id` 做 strict no-motion fixed-route consumer dry-run；再单独规划 route execution record、delivery/operator evidence、current live HIL 或 production readback。
