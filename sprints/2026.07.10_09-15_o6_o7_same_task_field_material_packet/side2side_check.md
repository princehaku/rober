# O6/O7 Same-Task Field Material Packet Side-by-Side Check

## 对照口径

1. 本轮必须消费同一 `task_id` 的准现场 route materials，而不是新增 wrapper-only surface。
2. Algorithm、O6、O7 三层必须对齐同一个 packet shape。
3. `map.yaml` 缺失可以是 optional gap，但不能阻断 `route.csv`、keyframes、route bag / rosbag、replay JSONL 的材料消费。
4. 所有层必须固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 验收结果

- Algorithm 输出 `trashbot.same_task_field_material_packet.v1`，包含 `material_summaries` 和 list-shaped `sample_refs`，验证 `Ran 62 tests in 0.347s OK`。
- O6 输出 `trashbot.o6.same_task_field_material_packet.v1`，返工后已读取 Algorithm actual shape 并回读 list-shaped `sample_refs` / per-material `material_sample_refs`，验证 `Ran 170 tests in 67.261s OK`。
- O7 consumer/UI 接住 O6 readback，兼容 `material_summaries`、`material_sample_refs`、`sample_ref_summaries` 和 legacy dict-shaped `sample_refs`，验证 `Tests 485 passed (485)`、build、lint 通过。
- 主会话验收 `git diff --check` 通过。

## 结论

本轮验收通过。它是准现场 same-task materials consumption，不是 delivery success 或 production cloud proof。

O6/O7 可以保守上调，因为本轮突破了上轮 hard gate 指出的“未消费新的真实或准现场 materials”缺口；O5/O1 不调整。
