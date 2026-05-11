# Sprint 2026.05.11 09-10 HIL pass and route replay crosscheck - Side2Side Check

## 状态

- 阶段：side2side check in-progress
- 时间：2026-05-11 16:47 Asia/Shanghai
- Owner：`autonomy-engineer`
- Scope：O3 fixed-route 与 task_record/diagnostics run-level 对账准备

## 对照结果

### O3 对照目标

- 同 run 使用统一 `evidence_ref` 的 fixed-route status + replay + task_record。
- `checkpoint/current_index/target/failure_code/evidence_ref` 最小闭环一致性。
- 无硬件时保证干跑样本可复验，提供缺样本可读输出。

### 本轮核验

- 执行 dry-run + offline unittest/py_compile，并通过 `scripts/evidence_crosscheck.py` 做 status/replay 对账。
- 输出样例：`route status -> progress`、`replay -> status`、`task_record.evidence_ref` 均 `PASS`。
- `python3 docs/navigation/fixed_route_workflow.md` 在当前仓库环境下不可执行（`SyntaxError`），属于环境工具链阻塞，不阻断字段复用本体。

### 复核样本

- 合成样本验证成功（status/task_record/replay 三方一致，`CHECK summary: mismatches=0`）。
- 真实 fixed-route/hardware 复盘样本在本轮无新增；task_record 与 route_replay 尚未完成同 run 串联实证。

### 不可放行项

- 未形成本轮真实 `hil_pass` 固定路线复盘样本。
- task_record 侧如未持久化 `route_progress`，脚本会以 `task_record nav_result.evidence` 兜底；若缺字段仍需在行为侧补齐。
