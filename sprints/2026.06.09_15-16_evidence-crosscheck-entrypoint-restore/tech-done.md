# sprint_type: micro

## 实际改动

- 新建 `pc-tools/evidence/evidence_crosscheck.py`：恢复 `evidence_crosscheck` 正式入口，支持 `--task-record-dir`、`--task-record`、`--evidence-ref`、`--hil-gate`（兼容 `--hil-gate-output`）、`--output-artifact`（兼容 `--rehearsal-artifact`）。
- 脚本实现固定路线 status JSON、software proof replay JSONL 与 task record 的同一 `evidence_ref` 轻量对账，输出包含 `task_record:` 与 `CHECK summary: mismatches=...`。
- 在输出/artifact 中加入不泄露 hardware 细节和 HIL 对齐失败的边界处理：软件对账 pass 时可写入 artifact，但 `hil_alignment_status` 与 `not_proven` 仍保持 `not_proven`，不宣称 real-route 或 real HIL pass。
- 同步更新 `pc-tools/evidence/README.md`：补充脚本用途、参数兼容别名、边界说明与证据边界约束。
- 该回归为微线程，不变更 board-live sprint、launch 文件或硬件配置。

## 验证结果

- `python3 pc-tools/evidence/evidence_crosscheck.py --help`
  - 通过
  - 关键片段：`--task-record-dir`、`--task-record`、`--evidence-ref`、`--hil-gate`、`--output-artifact` 均在帮助中可见
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_task_record.py`
  - 通过
  - 关键片段（与 smoke failure 相关）：`Ran 9 tests in ...`、`OK`
- `bash onboard/scripts/run_smoke_tests.sh`
  - 通过
  - 关键片段：`Ran 863 tests in ...` 与 `OK`
- `git diff --check -- pc-tools/evidence/evidence_crosscheck.py pc-tools/evidence/README.md onboard/src/ros2_trashbot_behavior/test/test_task_record.py sprints/2026.06.09_15-16_evidence-crosscheck-entrypoint-restore`
  - 通过，无空白错误
- `git status --short`
  - 有本次新增文件：`A pc-tools/evidence/evidence_crosscheck.py`、`A sprints/2026.06.09_15-16_evidence-crosscheck-entrypoint-restore/tech-done.md`、`M pc-tools/evidence/README.md`

## 剩余风险

- `evidence_crosscheck.py` 仍为软件证据边界工具；仍需真实实机或仿真链路补齐同一 `evidence_ref` 的 HIL、Nav2、任务完成材料后再用于现场闭环。
- 命令 `--hil-gate`/`--hil-gate-output` 与 `--output-artifact`/`--rehearsal-artifact` 采用同名兼容处理，后续可视团队习惯统一文档参数名。
