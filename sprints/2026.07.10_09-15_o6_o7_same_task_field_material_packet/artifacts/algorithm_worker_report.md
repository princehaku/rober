# Algorithm Worker Report

## 改动文件

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`

## 本轮实现

- 新增 `trashbot.same_task_field_material_packet.v1`，同时写入 manifest 顶层与 `field_motion_evidence_packet.same_task_field_material_packet`。
- packet 只读消费同一 `artifact_root` 的 `map.yaml`、`route.csv`、`keyframes`、`route_bag/rosbag`、`replay_jsonl`，输出安全材料摘要：
  - `present_materials` / `missing_materials`
  - 各材料 `basename`、`size_bytes`、`sha256_prefix`、`sample_refs`、`count`
  - `blocked_reasons`、`next_required_evidence`
  - 固定 false safety fields
- `map.yaml` 缺失会记录为 `same_task_field_material_map_yaml_missing_optional`，但不会阻止其它准现场材料被消费。
- 对 source manifest 里的危险 true、路径、token、raw、base64、credential、secret 做 fail-closed；packet 不回显原文。
- 更新 `same_task_mission_gate_artifact_delta`：当 gate ready 且 material packet ready 时，记录 `same_task_field_material_consumed=true`，但不把它升级成 `delivery_success` 或真实 live route execution 证明。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet
```

- `py_compile` 通过
- `unittest` 通过：`Ran 62 tests in 0.347s OK`
- `git diff --check` 通过

## Proof Boundary

- 证据边界：`software_proof_same_task_field_material_packet_only`
- 这只证明同一 `task_id` 的准现场路线材料已被 Algorithm 安全消费，并可供后续 O6/O7 读回/UI 展示。
- 不证明真实 production cloud、真实 live Nav2 route execution、真实机器人运动、真实 delivery record、真实 operator confirmation、真实 delivery success。

## 剩余风险

- O6/O7 侧尚未在本 worker 范围内接入 `same_task_field_material_packet` 的 readback/UI 合同。
- 当前 same-task 判定仍依赖已有 manifest lineage / `run_id` fallback；若后续需要更强的跨系统 task 对齐，还要补 O5/O6 task lineage 事实源。
