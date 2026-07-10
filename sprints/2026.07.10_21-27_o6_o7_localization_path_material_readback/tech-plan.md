# O6/O7 Localization Path Material Readback Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective 是 O5，约 `85%`。
2. 本 sprint 不针对 O5。
3. 理由：O5 缺真实 external production evidence；`cloud_production_cutover_readiness_packet` 已固定 `okr_credit_allowed=false`，继续做本地 probe、readback 或 support-only packet 不应计主 OKR 增量。O1 约 `90%`，但下一步必须是 current same-run HIL/path generation/route execution 材料；当前工作区没有这类 live artifacts。本轮转向 O6/O7，是为了消费最新 O1 `localization_path_material_bridge` 材料，并避免让 O7/operator 误读 cross-run clean-baseline path。

## Architecture

Data path:

`38_pc_summary_after_map_fix.json` -> Algorithm `field_route_evidence_manifest.py` -> O6 `remote_cloud_relay.py` archive/readback -> O7 `o7ConsumerReadAdapter.ts` / fixture preview panel.

New additive material name:

- Algorithm: `localization_path_material_readback`
- Schema: `trashbot.localization_path_material_readback.v1`
- Proof scope: `software_proof_localization_path_material_readback_only`
- O6 schema: `trashbot.o6.localization_path_material_readback.v1`
- O7 schema: `trashbot.pc_tools_workstation.o7_localization_path_material_readback.v1`

## Owner Work Packages

### Task A - Robot Algorithm Engineer

Allowed files:

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/tech-done.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/algorithm_worker_report.md`

Requirements:

- Add a `--localization-path-material-json` input that consumes the same-run localization/path readback shape used by O1, including `map_once_observed`, `amcl_pose_observed`, TF map-to-odom/map-to-base-link booleans, path generation requested/succeeded/generated fields, and point count.
- Emit `localization_path_material_readback` at top level and inside `field_motion_evidence_packet`.
- Keep same-run path false fields false for the default fixture input from artifact `38`.
- Add fail-closed tests for task mismatch, dangerous true fields, unsafe strings, and cross-run comparator confusion.

Validation commands:

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
rg -n "localization_path_material_readback|software_proof_localization_path_material_readback_only" onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback
```

### Task B - Robot Software Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/tech-done.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/o6_worker_report.md`

Requirements:

- Add O6 schema and sanitizer/readback for `localization_path_material_readback`.
- Support archive detail, field evidence, consumer detail, and `include=localization_path_material_readback`.
- Reject unsupported schema/proof scope, task mismatch, dangerous true fields, unsafe values, and inconsistent path success claims.
- Preserve fixed false safety fields.

Validation commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
rg -n "localization_path_material_readback|software_proof_localization_path_material_readback_only|include=localization_path_material_readback" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback
```

### Task C - Full-stack Software Engineer

Allowed files:

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/tech-done.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/o7_worker_report.md`

Requirements:

- Add O7 contract and consumer summary for `localization_path_material_readback`.
- Add fixture preview UI near the existing route/operator material sections.
- Show same-run localization/path fields, cross-run comparator boundary, blocked reasons, next required evidence, and fixed false safety flags.
- Keep UI read-only; do not add control, nav, TTS, submit, or motion actions.

Validation commands:

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
rg -n "localization_path_material_readback|software_proof_localization_path_material_readback_only|same_run_path" pc-tools/workstation/src pc-tools/workstation/test docs/product/pc_tools_workstation.md
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback
```

## Integration Acceptance

After workers return, Product closeout must verify:

- `tech-done.md` contains actual changed files, validation outputs, and remaining risk from all owners.
- O6/O7 do not expose raw payloads or sensitive fields.
- OKR.md and `docs/process/okr_progress_log.md` are updated only after Product decides whether this material consumption deserves a conservative O6/O7 increment.
- `side2side_check.md` and `final.md` are created for closeout.

