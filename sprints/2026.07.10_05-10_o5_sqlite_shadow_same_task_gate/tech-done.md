# 技术完成：O5 SQLite shadow same-task gate

## sprint_type

- sprint_type: epic
- 收口时间：2026-07-10 05-10 CST
- 主责 owner：Robot Software Engineer
- Product/OKR 收口：Product Manager / OKR Owner

## 实际改动

Robot Software 已完成并留档：

- `onboard/scripts/o5_same_task_mission_archive_smoke.py`
  - 新增 `--state-backend file|sqlite`，默认 `file` 保持上一轮兼容。
  - SQLite 模式使用 `build_server(..., state_backend="sqlite")`，terminal result 写入后关闭 relay，再用同一 SQLite state path 重启 relay 并读取 `GET /api/commands/<command_id>/result?robot_id=...`。
  - summary 新增并固定 `relay_state_backend=sqlite`、`relay_restart_readback=true`、`sqlite_state_store_reopened=true`、`connects_cloud_production=false`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- `onboard/tests/test_o5_same_task_mission_archive_smoke.py`
  - 覆盖 file 默认兼容路径和 SQLite restart/readback 路径。
  - 断言 `reconciliation.result_state=terminal_result_recorded` 与 `consumer.same_task_mission_gate_status=same_task_mission_gate_ready_not_success_proof`。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 说明 file/sqlite smoke 模式、summary 字段和 `software_proof_o5_sqlite_shadow_same_task_gate_only` 边界。
- `docs/product/cloud_4g_infrastructure.md`
  - 明确 SQLite shadow 不是 production cloud、production DB、queue 或多实例一致性证据。

Product/OKR 已完成：

- `OKR.md`
  - O5 从约 83% 保守上调到约 84%。
  - O6 维持约 84%，O7 维持约 83%。
  - 不归档任何 KR。
- `docs/process/okr_progress_log.md`
  - 新增 `2026-07-10 05-10｜o5_sqlite_shadow_same_task_gate` 收口记录。
- 本 sprint 新增 `tech-done.md`、`side2side_check.md`、`final.md` 和 `artifacts/product_worker_report.md`。

## 验证结果

Robot Software 验证证据：

- `python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py`
  - 通过，无输出。
- `python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke`
  - 通过：`Ran 3 tests in 2.282s`，`OK`。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 通过：`Ran 166 tests in 64.559s`，`OK`。
- `git diff --check -- ...`
  - 通过，无输出。

Product 收口验收：

- `rg -n "o5_sqlite_shadow_same_task_gate|software_proof_o5_sqlite_shadow_same_task_gate_only|sqlite_state_store_reopened|relay_restart_readback|same_task_mission_gate_ready_not_success_proof" OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate`
  - 通过，命中 OKR、progress log、Robot Software report 和 sprint 收口文档。
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/tech-done.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/side2side_check.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/final.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/artifacts/product_worker_report.md`
  - 通过，无输出。

## 剩余风险

- 本轮 proof boundary 是 `software_proof_o5_sqlite_shadow_same_task_gate_only`。
- 只证明本地 SQLite shadow store 的 relay restart/readback 与同一 `task_id` O6 same-task gate 串联。
- 不证明真实 production cloud、production DB、queue、多实例一致性、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实 live Nav2 route execution、真实 operator confirmation、真实手机/browser 或真实 delivery success。
- 下一轮继续 O5 只能接真实 production cloud、production DB/queue external probe 或 live endpoint evidence；否则应转向 O7 的 same-task mission material checklist，不再用 local shadow/smoke 提升 OKR 百分比。
