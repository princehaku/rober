# Sprint 2026.05.11 07-08 HIL proof and route replay - Side2Side Check

## 状态

- 阶段：side2side check completed
- 时间：2026-05-11 14:47 Asia/Shanghai
- Owner：`product-okr-owner`
- 目的：以 PRD/Tech Plan 验收口径做 run-level 对照收口。

## Completion classification

- Sprint overall：**Blocked**
- O1（HIL proof）：**Blocked**
- O3（route replay）：**Partial**
- O2（consistency replay）：**Partial**
- 依据：`evidence/run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30/` 下 `battery_once.jsonl`、`imu_once.jsonl`、`odom_once.jsonl`、`feedback_T1001.log` 均为 `status=BLOCKED`，`serial.log` 明确 `/dev/ttyUSB0` 不存在。

## O1 对照

- PRD 要求：一次真实 `hil_pass` + 全套文件 + `source=hil_pass`。
- 本轮结果：`hil_pass` 在运行阶段被 `serial` 设备缺失阻塞，未落盘实机文件。
- 对照：`status` 与 `--help` 命令成功，`move-test` 在 `hil_pass` 路径下报 `No such file or directory: /dev/ttyUSB0`。
- 结论：验收不通过（Blocked）。

## O3 对照

- PRD 要求：run 级 route replay 产生 `checkpoint/current_index/target/failure_code/evidence_ref`。
- 本轮结果：dry-run/静态校验通过（13 tests、py_compile），并补齐了 `route_progress` 在 `checkpoint/current_index/target/failure_code/evidence_ref` 维度的一致性；未有新实跑/回放样本。
- 对照：可重放性停留在静态测试层，缺少与 task_record 级联的实跑 `evidence_ref`。
- 结论：验收不通过（未满足“新增实跑复现”）。

## O2 对照

- PRD 要求：task record/diagnostics/route 失败场景可跨 `evidence_ref` 复核。
- 本轮结果：字段契约与静态测试通过，已支持 `failure_code/human_intervention_required/evidence_ref/state_transition_history`。
- 对照：缺少本轮失败/超时/取消 run 级记录，不构成增量复盘样本。
- 结论：仅满足软件契约，不满足 run-level 一致性复盘。

## 可放行项

- 可正式收口本轮为“Blocked 可追踪”闭环。
- 可将本轮记录用于下一轮的执行清单与风险归档。

## 不可放行项

- 不可将 O1 标记完成。
- 不可将 O2/O3 标记为新增实跑闭环。
- 不可将未落盘 `evidence_ref` 当作可复现链路。
