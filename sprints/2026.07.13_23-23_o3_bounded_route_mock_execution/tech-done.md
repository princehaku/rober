# Tech Done - O3 Bounded Route Mock Execution

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/`
- Owner: `robot-algorithm-engineer`
- Proof boundary: `software_proof_o3_o1_bounded_route_mock_execution_only`
- Status: implemented and locally verified

## 自主能力目标和本轮抓手

本轮抓手是消费 08:09 已接受的 `bounded_route_command_plan.json`，生成严格 no-motion 的 mock route execution simulation。它只证明 28-pose bounded route material 可以被离线执行进度消费者读取、校验并转成 27 条 segment completion mock progress events。

本轮不证明 live route execution、fixed-route movement、Nav2 controller/BT execution、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、delivery、HIL、safe-to-control 或 O5 production/external evidence。

## 实际改动

- 新增 `onboard/scripts/o3_bounded_route_mock_execution.py`
  - 新增 CLI `--bounded-plan` / `--output-dir`。
  - 写出 `bounded_route_mock_execution_summary.json` 和 `bounded_route_mock_execution_progress.jsonl`。
  - 写出前校验 source schema/status/identity/counts/no-motion guards/top-level false fields/`fixed_false_fields`/27 个 segment 顺序。
  - 输入漂移时返回非零，不写 artifact，并在 stderr 保留 false safety fields。
- 新增 `onboard/tests/test_o3_bounded_route_mock_execution.py`
  - 覆盖 valid plan 生成 27 条 mock progress events。
  - 覆盖 source schema drift、missing no-motion guard、`safe_to_control=true`、segment order drift 的 fail-closed 路径。
- 新增 `docs/navigation/bounded_route_mock_execution.md`
  - 记录输入契约、输出字段、false safety fields 和验收边界。
- 新增 artifacts：
  - `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json`
  - `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_progress.jsonl`

## 接口影响

- 新增离线 CLI，不 import ROS2，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不发送 NavigateToPose，不使用 WAVE ROVER UART。
- 新增 artifact schema：`trashbot.o3.bounded_route_mock_execution.v1`。
- 新增 progress event schema：`trashbot.o3.bounded_route_mock_execution.progress.v1`。
- 下游只应把本轮 artifact 当作 `software_proof_o3_o1_bounded_route_mock_execution_only`，不得升级为 live route execution 或 delivery evidence。

## 数据和样本输出变化

`bounded_route_mock_execution_summary.json` 关键字段：

- `schema=trashbot.o3.bounded_route_mock_execution.v1`
- `mock_execution_status=mock_route_execution_completed_not_live_route_execution`
- `proof_boundary=software_proof_o3_o1_bounded_route_mock_execution_only`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `segment_count=27`
- `mock_segment_progress_count=27`
- `progress_jsonl_event_count=27`
- `mock_total_distance_m=0.723849`
- `mock_total_elapsed_s=7.238`

`bounded_route_mock_execution_progress.jsonl` 共 27 行，`segment_index` 为 `0..26`。首条 event 为 `from_order=0`、`to_order=1`、`distance_m=0.025`、`elapsed_s=0.25`；末条 event 为 `from_order=26`、`to_order=27`、`distance_m=0.023849`、`elapsed_s=0.238`、`cumulative_distance_m=0.723849`。

固定 false 字段保持：

- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o3_bounded_route_mock_execution.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.tests.test_o3_bounded_route_mock_execution
```

结果：

```text
.....
----------------------------------------------------------------------
Ran 5 tests in 0.005s

OK
```

```bash
python3 onboard/scripts/o3_bounded_route_mock_execution.py \
  --bounded-plan sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json \
  --output-dir sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm
```

结果：

```json
{"mock_execution_status": "mock_route_execution_completed_not_live_route_execution", "mock_segment_progress_count": 27, "progress": "sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_progress.jsonl", "route_execution_success": false, "safe_to_control": false, "status": "ok", "summary": "sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json"}
```

```bash
python3 -m json.tool sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json >/dev/null
```

结果：通过，无输出。

```bash
python3 - <<'PY'
...
PY
```

结果：

```text
bounded_route_mock_execution_acceptance_ok
```

```bash
rg -n "bounded_route_mock_execution|mock_route_execution_completed_not_live_route_execution|software_proof_o3_o1_bounded_route_mock_execution_only|route_execution_success=false|safe_to_control=false" \
  onboard/scripts/o3_bounded_route_mock_execution.py \
  onboard/tests/test_o3_bounded_route_mock_execution.py \
  docs/navigation/bounded_route_mock_execution.md \
  sprints/2026.07.13_23-23_o3_bounded_route_mock_execution
```

结果：通过，命中脚本、测试、导航文档、tech-plan、pre_start、summary 和 progress JSONL 中的 acceptance anchors。

```bash
git diff --check -- \
  onboard/scripts/o3_bounded_route_mock_execution.py \
  onboard/tests/test_o3_bounded_route_mock_execution.py \
  docs/navigation/bounded_route_mock_execution.md \
  sprints/2026.07.13_23-23_o3_bounded_route_mock_execution
```

结果：通过，无输出。

## 失败定位

本轮验收命令未出现失败。新增单测覆盖了以下 fail-closed 场景：

- source schema drift
- no-motion guard 缺失
- `safe_to_control=true`
- segment 顺序漂移

## 剩余风险

- 本轮是 local/mock route progress simulation，只是软件 proof，不是 live route execution。
- `mock_total_elapsed_s` 来源是 `distance_m / planned_linear_speed_cap_mps` 的 deterministic mock 计算，不是 controller feedback 或墙钟执行时间。
- 尚未证明 current live safety gate、stop/HIL capture、同窗口 `/scan`/localization/TF readiness、Nav2/controller result、delivery/operator acceptance 或 safe-to-control。
- 下一步能力建设应在 explicit operator approval 和安全围栏齐备后，采集 current live stop/HIL evidence；再由 Algorithm 在同一 live window 记录 route execution/controller result evidence。
