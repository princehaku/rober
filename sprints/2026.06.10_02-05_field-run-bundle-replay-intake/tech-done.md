# sprint_type: micro

## 实际改动

- 为 `onboard/scripts/field_route_evidence_manifest.py` 增加真实 field run bundle 布局扫描，支持 `map/*.yaml`、`route/route.csv`、`route/keyframes/`，同时兼容旧同层与 `route_data/` 结构。
- 新增 `--derive-replay-jsonl`，从 `route.csv` 只读派生 deterministic replay JSONL，供 manifest gate 和 O7/PC consumer 使用，并保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 扩展 `onboard/tests/test_field_route_evidence_manifest.py`，覆盖真实 bundle intake、缺失 `route_bag` fail closed、派生 replay 不含绝对路径与控制命令。
- 更新 `docs/navigation/field_route_evidence_manifest.md`，补充真实 run bundle intake、derive replay 用法和 fail-closed 边界。
- 更新 `docs/navigation/fixed_route_workflow.md`，把真实路线采集后的 field evidence manifest 生成入口纳入固定路线工作流。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_manifest.py`
  - 结果：`Ran 12 tests in 0.063s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
  - 结果：通过，无语法错误输出。
- `python3 onboard/scripts/field_route_evidence_manifest.py --mode local --input sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts --derive-replay-jsonl sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/derived_replay.jsonl --output sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/field_run_manifest.json --run-id field_run_bundle_replay_intake_20260610`
  - 结果：脚本按预期返回非零，stdout 为 `{"gate_pass": false, "output": "sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/field_run_manifest.json", "schema": "trashbot.field_evidence_manifest.v1", "status": "blocked_artifacts_missing"}`。
  - 只读检查确认：
    - `derived_replay.frame_count == 17`
    - `gate_pass == false`
    - `blocked_reason == missing_required_artifact`
    - `safe_to_control == false`
    - `delivery_success == false`
    - `primary_actions_enabled == false`
    - `artifacts.rosbag.present == false`
    - `artifacts.rosbag.required == true`
    - `artifacts.replay_jsonl.present == true`
  - 结论：01-15 真实 bundle 因缺 `route_bag` / `rosbag` 继续 fail closed，但 O7-safe `derived_replay.jsonl` 已成功生成。
- `python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route --map-yaml sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.yaml --map-pgm sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.pgm --derive-replay-jsonl sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/derived_replay_route_only.jsonl --output sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/field_run_manifest_route_only.json --run-id field_run_bundle_replay_intake_route_only_20260610`
  - 结果：脚本按预期返回非零，stdout 为 `{"gate_pass": false, "output": "sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/field_run_manifest_route_only.json", "schema": "trashbot.field_evidence_manifest.v1", "status": "blocked_artifacts_missing"}`。
  - 只读检查确认：
    - `derived_replay.frame_count == 17`
    - `gate_pass == false`
    - `blocked_reason == missing_required_artifact`
    - `missing_required == ["rosbag"]`
    - `artifacts.rosbag.required == true`
    - `artifacts.replay_jsonl.required == true`
    - `artifacts.replay_jsonl.present == true`

## 剩余风险

- 派生 replay 仅基于 `route.csv` 位姿事实，不包含 rosbag、速度、控制闭环或送达成功语义；真实路线成功仍需现场 run bundle 的 rosbag 与后续验收材料证明。
