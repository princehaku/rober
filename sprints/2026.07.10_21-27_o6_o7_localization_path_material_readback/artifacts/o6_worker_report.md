# O6 Worker Report

## 实际改动文件

1. `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
2. `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
3. `docs/interfaces/o6_cloud_archive_api.md`
4. `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/o6_worker_report.md`

## 实现内容

- 为 O6 新增 `localization_path_material_readback` additive section，输入 schema `trashbot.localization_path_material_readback.v1`，回读 schema `trashbot.o6.localization_path_material_readback.v1`，proof scope 固定为 `software_proof_localization_path_material_readback_only`。
- 支持从 `field_evidence_manifest`、`artifact_bundle` 和 `field_motion_evidence_packet.localization_path_material_readback` 读取材料，并在 archive detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=localization_path_material_readback` 中回读。
- fail-closed 规则已加：schema/proof scope 不匹配、task mismatch、unsafe text/path/url/token/traceback/response body、cross-run override claim、same-run path success claim 都会把本 section 降级为 `blocked_not_proven`。
- same-run path 结论被固定为只读 false：`same_run_path_generation_succeeded=false`、`same_run_path_generated=false`、`same_run_path_point_count=0`、`same_run_path_proven=false`。
- cross-run clean-baseline comparator 只通过 `cross_run_clean_baseline_*` 字段展示，不允许覆盖 same-run false 结论。
- 新增 O6 单测覆盖 field-evidence/bundle 正向 readback、consumer include、missing/schema/scope/task mismatch、unsafe text 和 same-run path success claim 负向路径。

## 验证命令输出结果

```text
$ python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
exit 0
```

```text
$ python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 181 tests in 77.953s
OK
```

```text
$ rg -n "localization_path_material_readback|software_proof_localization_path_material_readback_only|include=localization_path_material_readback" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md
命中 remote_cloud_relay.py / test_remote_cloud_relay.py / docs/interfaces/o6_cloud_archive_api.md 中的新 schema、proof scope、consumer include 与文档说明。
```

```text
$ git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback
exit 0
```

## 失败定位

- 首轮单测失败点：`test_o6_localization_path_material_readback_in_field_and_bundle_readback` 在二次 archive/detail readback 时拿不到 `cross_run_clean_baseline_path_summary.path_point_count`。
- 根因：第一次 ingest 后的 comparator 已是结构化 O6 摘要，二次经过 `_o6_localization_path_material_readback_comparator_summary()` 时被误判成 generic material summary，导致 `path_point_count` 被折叠丢失。
- 修复：优先识别结构化 comparator 字段集合（`path_point_count`、`path_generation_*`、`same_run_override_allowed` 等），保留 comparator 语义而不是再次物化成 basename/count 摘要。

## 剩余风险

- 当前仅完成 O6 archive/readback/support-only proof，未验证 Algorithm worker 最终产出的实际 artifact 形状是否与本合同完全一致；若 Algorithm 命名或字段稍有偏差，会按 fail-closed 降级为 `blocked_not_proven`。
- 本轮不证明真实 live Nav2 path generation、route execution、delivery success、safe-to-control、HIL 或 production cloud。
- O7 UI/consumer 尚需并行 worker 完成最终展示和 fixture 适配，本报告只覆盖 O6 侧合同与 readback。
