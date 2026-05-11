# Tech Done: O2 Task Recovery Route Replay Docker Proof

## 实际改动

- `task_orchestrator.py`：fixed-route status 的嵌套 `route_progress` 保留原文，并提升完整兼容字段集；`_derive_evidence_ref()` 明确支持 `evidence.route_progress.evidence_ref`。
- `scripts/evidence_crosscheck.py`：`--task-record-dir` 查找扩展到 task record 顶层、top-level route_progress 和 nav evidence route_progress；未显式传入 task record/path/dir 时只检查 status/replay，不再隐式扫默认 task 目录。
- `test_task_orchestrator_collection_execution.py`：扩展嵌套 `route_progress` promotion 覆盖。
- `test_task_record.py`：扩展 `--task-record-dir` 基于 nav route_progress evidence_ref 匹配的回归覆盖。
- `OKR.md`：O2/O3 software proof 更新到约 77%，O1 保持约 75% blocked。

## 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  scripts/evidence_crosscheck.py
```

结果：exit 0。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py \
  src/ros2_trashbot_behavior/test/test_task_record.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

结果：`Ran 46 tests in 0.131s`，`OK`。

`scripts/evidence_crosscheck.py` 手工样例：

- success sample：`--task-record-dir` 找到同 `evidence_ref=run-o2-route-progress-proof` 的 task record，输出 `CHECK summary: mismatches=0`。
- failure sample：`--task-record-dir` 搭配缺匹配 `evidence_ref=missing-run`，输出 `CHECK summary: mismatches=2`，命令返回 `missing_match_exit=1`。

Scoped diff check：

```bash
git diff --check -- OKR.md scripts/evidence_crosscheck.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_record.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/pre_start.md sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/prd.md sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/tech-plan.md sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/tech-done.md sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/side2side_check.md sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/final.md
```

结果：exit 0。

补充：新建 sprint docs 因未跟踪文件不会被普通 `git diff --check` 覆盖，已逐个执行 `git diff --check --no-index /dev/null <new-doc>`，结果 `untracked_sprint_docs_diff_check=ok`。

## 偏差

- 未修改硬件 docs/scripts。
- 未触碰 `sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/*`。
- 未声明 `hil_pass`。

## 剩余风险

- 真实 WAVE ROVER 串口与 Nav2/fixed-route 上车 proof 仍缺失。
