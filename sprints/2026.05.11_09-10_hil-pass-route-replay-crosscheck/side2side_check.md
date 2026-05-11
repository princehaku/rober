# Sprint 2026.05.11 09-10 HIL pass and route replay crosscheck - Side2Side Check

## 状态

- 阶段：side2side check in-progress
- 时间：2026-05-11 16:47 Asia/Shanghai
- Owner：`autonomy-engineer`
- Scope：O3 fixed-route 与 task_record/diagnostics run-level 对账准备
- Scope：已补充 O1 上位/硬件 run-level 失败阻塞记录，保留 O2/O3 待上车复核

## 对照结果

### O3 对照目标

- 同 run 使用统一 `evidence_ref` 的 fixed-route status + replay + task_record。
- `checkpoint/current_index/target/failure_code/evidence_ref` 最小闭环一致性。
- 无硬件时保证干跑样本可复验，提供缺样本可读输出。

- O1 关联目标（本轮新增）

- 使用 run-level `run_20260511T094018Z_hil_pass_speed0p050_dur0p30` 完成一次 HIL `hil_pass` 尝试，当前阻塞于 `source=software_proof` -> `source=hil_pass` 切换未完成。
- 阻塞核验项：`/dev/ttyUSB0` 不存在，阻断 `feedback_T1001/odom_once/imu_once/battery_once` 的真实采样。

### 本轮核验

- 执行 dry-run + offline unittest/py_compile，并通过 `scripts/evidence_crosscheck.py` 做 status/replay 对账。
- 输出样例：`route status -> progress`、`replay -> status`、`task_record.evidence_ref` 均 `PASS`。
- `python3 docs/navigation/fixed_route_workflow.md` 在当前仓库环境下不可执行（`SyntaxError`），属于环境工具链阻塞，不阻断字段复用本体。

### 复核样本

- 合成样本验证成功（status/task_record/replay 三方一致，`CHECK summary: mismatches=0`）。
- 真实 fixed-route/hardware 复盘样本在本轮无新增；task_record 与 route_replay 尚未完成同 run 串联实证。
- O1 HIL 硬件 smoke 在 `run_20260511T094018Z_hil_pass_speed0p050_dur0p30` 阻塞，未能产生真实闭环 `feedback/odom/imu/battery` 证据。
- O2/O3 后续 evidence 串联依赖：
  - 首先恢复串口可见性（主机挂载/权限）后复跑该 run 或新 run；
  - 成功后同步补齐 `route` 与 `task_record` 侧 `evidence_ref` 一致性检查。

### 新增对账对齐核验（本轮最小修复）

- `evidence_ref/result_path/failure_code/human_intervention_required/state_transition_history` 使用统一回溯函数重算后，对齐网关 status 与 diagnostics 输出。
- 重点验证：
  - `task_record` 存在且完整时，diagnostics 使用 task_record 作为权威；
  - `task_record` 读不到/损坏时，fallback 到 `last_task.state_transition_history` 优先于 `latest_status`，并且 `last_task.evidence_ref` 在缺省时回退 `result_path` 以保留历史兼容行为。
- 新增 unittest 样本已覆盖上述两类场景，确认 `failure/state_transition_history` 不再与 status 脱节。

### 不可放行项

- 未形成本轮真实 `hil_pass` 固定路线复盘样本。
- task_record 侧如未持久化 `route_progress`，脚本会以 `task_record nav_result.evidence` 兜底；若缺字段仍需在行为侧补齐。
