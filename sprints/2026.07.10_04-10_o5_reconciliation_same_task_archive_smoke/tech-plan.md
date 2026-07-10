# O5 Reconciliation Same-Task Archive Smoke Tech Plan

## 方案

本轮以 O5 relay reconciliation 为源材料：

1. `field_route_evidence_manifest.py` 在 `--cloud-terminal-result-json` 读取到 `trashbot.cloud_command_result_reconciliation.v2` 时，校验 `result_state=terminal_result_recorded`、nested `terminal_result.schema=trashbot.cloud_command_terminal_result.v1`、safe refs、dangerous true 和 task alignment，再沿用现有 `delivery_result_evidence` 输出。
2. 新增或扩展本地 smoke：启动 in-process relay，提交 command，写入 robot-facing terminal result，GET reconciliation v2，将该 JSON 传给 manifest，POST 到 O6 `/api/o6/archive/field-evidence`，再 GET `/api/o6/consumer/tasks/<task_id>?include=same_task_mission_evidence_gate`。
3. smoke 输出只返回 schema、task_id、command_id、manifest gate、O6 write/readback status、same-task gate status、proof boundary 和 false safety flags。

## 文件范围

Algorithm owner 可改：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/algorithm_worker_report.md`

Robot Software owner 可改：

- `onboard/scripts/o5_same_task_mission_archive_smoke.py`（如需新增）
- `onboard/tests/test_o5_same_task_mission_archive_smoke.py`（如需新增）
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`（如选择直接扩展 relay 集成测试）
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/software_worker_report.md`

Product owner 可改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/tech-done.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/side2side_check.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/final.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/product_worker_report.md`

范围外不得修改硬件配置、vendor 文件、launch 硬件参数、WAVE ROVER 协议或无关 UI。

## 接口影响

- `--cloud-terminal-result-json` 向后兼容 direct `trashbot.cloud_command_terminal_result.v1`。
- 新增兼容 `trashbot.cloud_command_result_reconciliation.v2` wrapper，但输出仍使用现有 `delivery_result_evidence` 与 `same_task_mission_evidence_gate` 合同。
- O6/O7 现有读取路径不应破坏。

## 验收命令

Algorithm:

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

Robot Software:

```bash
python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py
python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

Product / integration:

```bash
git diff --check
rg -n "o5_reconciliation_same_task_archive_smoke|software_proof_o5_reconciliation_same_task_archive_smoke_only|same_task_mission_gate_ready_not_success_proof" OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke
```

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低活跃 Objective 是 O5：约 82%。
2. 本 sprint 针对 O5，并以 O6 archive/readback 作为消费侧证明。
3. 不选 O7/O6/O1 的理由：O7/O6 当前略高于 O5，O1 缺真实硬件/HIL；本轮 O5 可用本地 relay/mock production-adjacent material 推进，不需要真实硬件。

## 风险边界

- 验证成功只证明本地 relay reconciliation material 进入 same-task gate 和 O6 archive/readback。
- 不证明 production cloud、真实 HTTPS/TLS/4G、真实 live Nav2、真实送达、真实 OSS/CDN 或真实手机/browser。
- 如果 `test_remote_cloud_relay` 运行耗时过长，Robot Software 可先跑新增 targeted smoke test，但必须在报告中写清完整 O6 回归是否已跑。
