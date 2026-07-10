# 技术计划：O5 SQLite shadow same-task gate

## OKR 最低优先级核对

当前 `OKR.md` 4.1 中最低活跃 Objective 为：

- O5：约 83%
- O7：约 83%

本 sprint 针对 O5。选择原因：上一轮明确建议 O5 只有在消费 production-like endpoint / DB / queue material 或准现场 same-task material 时才继续。本轮能在当前环境中推进 SQLite state backend + relay restart/readback，同一 `task_id` 的 command/result/reconciliation 进入 O6 gate；O7 若只新增展示面板会落入 support-only。

## Owner 分工

### Robot Software Engineer

文件范围：

- `onboard/scripts/o5_same_task_mission_archive_smoke.py`
- `onboard/tests/test_o5_same_task_mission_archive_smoke.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`（仅当需要覆盖 SQLite terminal result/reconciliation restart 行为）
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`
- `sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/artifacts/software_worker_report.md`

任务：

- 保持现有 file smoke 兼容。
- 新增 SQLite shadow smoke 模式，并在 terminal result 写入后重启 relay，再读 reconciliation。
- summary 增加 backend/restart/readback 字段和 false safety fields。
- 增加单元测试和必要文档。

验收命令：

```bash
python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py
python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check -- onboard/scripts/o5_same_task_mission_archive_smoke.py onboard/tests/test_o5_same_task_mission_archive_smoke.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/artifacts/software_worker_report.md
```

### Product Manager / OKR Owner

文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/tech-done.md`
- `sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/side2side_check.md`
- `sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/final.md`
- `sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/artifacts/product_worker_report.md`

任务：

- 根据 Robot Software 验证证据保守更新 O5 进度与 progress log。
- 明确 proof boundary：SQLite shadow software proof，不是 production DB/queue。
- 不归档 KR，除非出现真实 production cloud / DB / queue / live route evidence。

验收命令：

```bash
rg -n "o5_sqlite_shadow_same_task_gate|software_proof_o5_sqlite_shadow_same_task_gate_only|sqlite_state_store_reopened|relay_restart_readback|same_task_mission_gate_ready_not_success_proof" OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/tech-done.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/side2side_check.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/final.md sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/artifacts/product_worker_report.md
```

## 接口影响

- 不改变 O5 HTTP API shape。
- 不改变 O6 archive/readback API shape。
- smoke summary 新增字段只用于本轮 artifact 和测试。

## 风险边界

- SQLite backend 是单机 shadow proof，不能写成 production DB/queue ready。
- 重启 readback 只证明 state 可恢复，不证明多实例一致性、队列 worker cutover、备份恢复或灾备。
- mock route/nav/delivery fixture 保持 false safety fields，不能宣称 delivery success。
