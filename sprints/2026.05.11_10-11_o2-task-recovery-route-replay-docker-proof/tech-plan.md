# Tech Plan: O2 Task Recovery Route Replay Docker Proof

## 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `scripts/evidence_crosscheck.py`
- behavior/script 相关现有 tests
- `OKR.md`
- 本 sprint 目录

## 设计

1. 在 `_fixed_route_status_evidence()` 内保持原始 `route_progress`，并把嵌套 progress 中的兼容字段提升到 top-level evidence。
2. 在 `_derive_evidence_ref()` 中显式回看 `evidence.route_progress.evidence_ref`，确保只嵌套时也能形成 run-level anchor。
3. 保持 `write_task_record(route_progress=...)` API，并在缺参时从最后一个 nav result 的 evidence 抽取。
4. `operator_gateway` 和 diagnostics 继续使用统一 traceability coalesce；diagnostics 的 route_progress 提取跳过空 `{}` 并继续查 nav evidence。
5. `evidence_crosscheck.py --task-record-dir` 仅在显式传入目录时自动查找 task record；缺匹配即 mismatch。查找范围扩展到顶层、top-level route_progress 和 nav evidence route_progress 的 `evidence_ref`。

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  scripts/evidence_crosscheck.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py \
  src/ros2_trashbot_behavior/test/test_task_record.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

还需运行：

- `scripts/evidence_crosscheck.py` 成功样例：带 `--task-record-dir`。
- `scripts/evidence_crosscheck.py` 失败样例：缺匹配 task record 或缺 route_progress。
- scoped `git diff --check`，仅覆盖本轮允许改动文件。

## 风险边界

- 本轮 evidence 是 software proof。
- O1/HIL 仍 blocked，不用 O2/O3 软件复账结果冒充 real hardware pass。
