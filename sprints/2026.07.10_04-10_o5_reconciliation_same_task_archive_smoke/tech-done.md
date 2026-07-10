# O5 Reconciliation Same-Task Archive Smoke Tech Done

## Sprint Type

sprint_type: epic

## 实际改动

Algorithm worker 已完成：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/algorithm_worker_report.md`

Algorithm 改动把 `--cloud-terminal-result-json` 扩展为兼容 `trashbot.cloud_command_result_reconciliation.v2` wrapper。只有 `result_state=terminal_result_recorded` 且 nested `terminal_result.schema=trashbot.cloud_command_terminal_result.v1` 时才下钻；输出仍是 `trashbot.delivery_result_evidence.v1` / `source_schema=trashbot.cloud_command_terminal_result.v1`，避免把 reconciliation wrapper 本身升级成 mission success 证据。

Robot Software worker 已完成：

- `onboard/scripts/o5_same_task_mission_archive_smoke.py`
- `onboard/tests/test_o5_same_task_mission_archive_smoke.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/software_worker_report.md`

Robot Software 改动新增可复跑本地 smoke，串起 `POST /api/commands/confirm-dropoff`、terminal result write、`GET /api/commands/<command_id>/result`、Algorithm manifest、`POST /api/o6/archive/field-evidence` 和 `GET /api/o6/consumer/tasks/<task_id>?include=same_task_mission_evidence_gate`，最终读回 `same_task_mission_gate_ready_not_success_proof`。

Product closeout 已完成：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/tech-done.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/side2side_check.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/final.md`
- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/product_worker_report.md`

## 验证结果

Algorithm worker 记录：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
exit 0

python3 -m unittest onboard.tests.test_field_route_evidence_manifest
Ran 58 tests in 0.304s
OK

git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/algorithm_worker_report.md
exit 0
```

Robot Software worker 记录：

```text
python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py
exit 0

python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke
Ran 2 tests in 1.180s
OK

python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 166 tests in 64.457s
OK

git diff --check -- onboard/scripts/o5_same_task_mission_archive_smoke.py onboard/tests/test_o5_same_task_mission_archive_smoke.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/software_worker_report.md
exit 0
```

Product closeout validation：

```text
rg -n "o5_reconciliation_same_task_archive_smoke|software_proof_o5_reconciliation_same_task_archive_smoke_only|same_task_mission_gate_ready_not_success_proof|trashbot.cloud_command_result_reconciliation.v2|2026.07.10_04-10" OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke
exit 0
key hits: OKR.md:106, OKR.md:160, OKR.md:232, docs/process/okr_progress_log.md:11, docs/process/okr_progress_log.md:13, docs/process/okr_progress_log.md:17

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/tech-done.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/side2side_check.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/final.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/product_worker_report.md
exit 0
```

## 偏差

- 本轮实现符合 PRD 范围：不是继续做只读 review / wrapper-only 文档，而是用 relay reconciliation material 进入 manifest、archive 和 consumer readback。
- 本轮仍是 local/mock smoke。它使用 mock Nav2 proof、mock route bag pose progress、mock `route.csv` / keyframe / replay，不启动真实 Nav2、不发送 `/cmd_vel`、不连接真实公网或 4G。
- O7 未新增 UI 或 browser 验收证据，因此 Product 不上调 O7。

## 剩余风险

- `software_proof_o5_reconciliation_same_task_archive_smoke_only` 不证明真实 production cloud、真实 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实手机/browser 或真实 delivery success。
- `same_task_mission_gate_ready_not_success_proof` 只能表示同一 `task_id` 的本地/mock terminal material 与 mission 摘要可被安全读回，不等于送达成功。
- Product 未直接修改产品代码；代码注释比例与中文注释规范由 Engineer 改动和回归测试兜底，本轮 closeout 不把该项提升为生产准入证据。
