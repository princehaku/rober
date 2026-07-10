# Robot Software Worker Report

## 实际改动

- `onboard/scripts/o5_same_task_mission_archive_smoke.py`
  - 将 smoke 证明边界更新为 `software_proof_o5_sqlite_shadow_same_task_gate_only`。
  - 新增 `--state-backend file|sqlite`，默认 `file` 保持原 file smoke 兼容。
  - 新增 SQLite shadow restart/readback：terminal result 写入后关闭 relay，再用同一 SQLite state path 通过 `build_server(..., state_backend="sqlite")` 重启，并读取 `GET /api/commands/<command_id>/result?robot_id=...`。
  - summary 新增 `relay_state_backend`、`relay_restart_readback`、`sqlite_state_store_reopened`、`connects_cloud_production=false`，并继续固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- `onboard/tests/test_o5_same_task_mission_archive_smoke.py`
  - 保留 file 默认路径断言，补充 backend/restart 字段的 file 兼容期望。
  - 新增 SQLite restart/readback 单测，断言 `relay_state_backend=sqlite`、`relay_restart_readback=true`、`sqlite_state_store_reopened=true`、`reconciliation.result_state=terminal_result_recorded` 和 `consumer.same_task_mission_gate_status=same_task_mission_gate_ready_not_success_proof`。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 更新 O5 same-task smoke 说明，写明 file 默认兼容、SQLite shadow restart/readback、summary 字段和 proof boundary。
- `docs/product/cloud_4g_infrastructure.md`
  - 更新云中转控制面文档，明确 SQLite shadow 不是 production cloud、production DB、queue 或多实例一致性证据。

`onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 本轮只运行验证；文件在工作树中已有修改状态，但本 worker 没有编辑它。

## 验证结果

- `python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py`
  - 通过，无输出。
- `python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke`
  - 通过：`Ran 3 tests in 2.282s`，`OK`。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 通过：`Ran 166 tests in 64.559s`，`OK`。
- `git diff --check -- ...`
  - 通过，无输出。

## 剩余风险

- 本轮证据边界是 `software_proof_o5_sqlite_shadow_same_task_gate_only`，只证明本地 SQLite shadow store 的 relay restart/readback 与 O6 same-task gate 串联。
- 不证明真实 production cloud、production DB、queue、多实例一致性、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实 live Nav2 route execution、真实 operator confirmation、真实手机/browser 或真实 delivery success。
