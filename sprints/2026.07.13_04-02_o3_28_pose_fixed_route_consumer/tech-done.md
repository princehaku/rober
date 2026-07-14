# Tech Done - O3 28-Pose Fixed Route Consumer

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/`
- Owner: `robot-algorithm-engineer`
- Status: implementation and verification passed
- Proof boundary: `software_proof_o3_o1_strict_no_motion_fresh_28_pose_fixed_route_consumer_only`

## 自主能力目标和本轮抓手

本轮目标是把 03:00 fresh same-run `path_structured_pose_count=28` 材料接入 fixed-route / route-intent consumer，替代 01:00 对旧 21:57 partial stdout-tail 的 primary 依赖。

本轮抓手是新增 artifact-only Algorithm consumer：先校验 `path_generated=true`、`fresh_live_artifact_used=true`、`historic_21_57_artifact_reused_as_live_proof=false` 和 28 个完整 `proof.path_structured_poses`，再输出 strict no-motion summary、route replay JSONL 和 route CSV。

## 改动文件和接口影响

- `onboard/scripts/o3_28_pose_fixed_route_consumer.py`
- `onboard/tests/test_o3_28_pose_fixed_route_consumer.py`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_consumer_summary.json`
- `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_replay.jsonl`
- `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_route.csv`
- `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/tech-done.md`

接口影响：新增离线脚本，不改 ROS2 runtime、launch、controller、BT、Nav2 action、`/cmd_vel`、`/api/base/manual` 或 WAVE ROVER UART。新 route identity 为 `route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path` / `task_o3_28_pose_fixed_route_consumer_20260713_0402`。

## 实现内容

`o3_28_pose_fixed_route_consumer.py` 新增 fail-closed 输入校验：顶层 summary 和 `proof` 都必须保持 path generated、28 structured poses、fresh live artifact、旧 21:57 非 live proof，以及全部 no-motion safety false。若 pose 缺失、`source_index` 不连续、frame/stamp/position/orientation 字段缺失，脚本直接失败，不生成可消费材料。

输出 summary 固定：

- `fresh_28_pose_structured_material_consumed=true`
- `historic_21_57_artifact_primary_source=false`
- `path_structured_pose_count=28`
- `validation_status=pass_fresh_28_pose_structured_material`
- `dry_run_status=accepted_strict_no_motion_28_pose_consumer_material`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`

`fixed_route_28_pose_replay.jsonl` 写出 28 行 `event=structured_pose`。`fixed_route_28_pose_route.csv` 写出 header + 28 行，覆盖 order、source_index、frame、stamp、position 和 orientation。

`docs/navigation/fixed_route_workflow.md` 增加 2026-07-13 04:02 规则：consumer primary source 应改为 03:00 fresh 28-pose structured material，旧 21:57 partial stdout-tail 只能作为 comparator。

## 测试、dry-run 或上车验证结果

已运行验收命令并通过：

```text
python3 -m py_compile onboard/scripts/o3_28_pose_fixed_route_consumer.py
# exit 0

python3 -m unittest onboard.tests.test_o3_28_pose_fixed_route_consumer
....
Ran 4 tests in 0.004s
OK

python3 onboard/scripts/o3_28_pose_fixed_route_consumer.py --source-summary ... --output-dir ...
{"status": "ok", "summary": "sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_consumer_summary.json"}

python3 -m json.tool .../fixed_route_28_pose_consumer_summary.json >/tmp/o3_28_pose_fixed_route_consumer_summary.pretty.json
# exit 0

structured assertions
o3_28_pose_fixed_route_consumer_ok

rg -n "28|path_structured_pose_count|fixed-route|route_intent_id|task_id|route_execution_success|delivery_success|hil_pass|safe_to_control|historic_21_57" ...
# anchors found in sprint artifacts and docs/navigation/fixed_route_workflow.md

git diff --check -- onboard/scripts/o3_28_pose_fixed_route_consumer.py onboard/tests/test_o3_28_pose_fixed_route_consumer.py docs/navigation/fixed_route_workflow.md sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer
# exit 0
```

## 数据、样本或调试输出变化

- Summary primary source: `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_summary.json`
- Summary primary source SHA256: `cb528016c7086a8b30dc98af0275a83f677d4801196bc70ac5a9892562605551`
- JSONL 行数：28 structured pose events
- CSV 行数：header + 28 route rows
- First pose: `source_index=0`, `frame_id=map`, `x=0.07615115310756959`, `y=0.2500000037252903`
- Last pose: `source_index=27`, `frame_id=map`, `x=0.8`, `y=0.2500000037252903`

## 失败定位

本轮实现和验收没有出现失败。脚本内已把可能的失败定位收敛到输入合同：非 fresh source、旧 21:57 被标为 live proof、pose count 非 28、pose 字段缺失或 source_index 不连续、安全字段不为 false 时都会 fail closed。

## 剩余风险和下一步能力建设建议

剩余风险：

- 本轮仍是 artifact-only strict no-motion consumer material，不是 route execution、fixed-route movement、NavigateToPose、controller/BT、delivery、HIL 或 safe-to-control。
- 03:00 source 的 28-pose 路线来自 `map_bounds_adapted_no_motion_planner_probe`，没有复现旧 21-pose expectation；若产品仍要求 21 点，下一步 blocker 是 current live localization/map-bound drift。
- route material 已可消费，但还缺后续同一 `route_intent_id` 的 explicit route execution record、delivery/operator acceptance、current live HIL 和 production external evidence。

下一步建议：基于本轮 `fixed_route_28_pose_route.csv` 做 strict no-motion route replay/consumer integration；再单独规划受控 route execution 证据，且继续保持 no `/cmd_vel`、no `/api/base/manual`、no WAVE ROVER UART，直到有明确安全准入。
