# Sprint 2026.05.11 08-09 HIL pass and route replay - Side2Side Check

## 状态

- 阶段：side2side check completed
- 时间：2026-05-11 16:35 Asia/Shanghai
- Owner：`autonomy-engineer`
- 结论：按 PRD/Tech Plan 验收口径收口。

## Completion classification

- Sprint overall：**Partial**
- O1（HIL proof）：**Not executed in this scope**
- O3（route replay）：**Partial**
- 依据：本轮未创建新的 hil run；已完成 O3 软件复盘契约，未形成同 run 真机 route replay 产物。

## 对照结果

### O3 对照

- PRD/Tech 目标：同一 run 的 fixed-route replay 要与 task/task_record 字段可复盘。
- 实测：
  - `route_progress` 字段结构在 dry-run 中保持与 payload 头的 `checkpoint/current_index/target/failure_code/evidence_ref` 对齐。
  - replay jsonl 行包含 `evidence_ref` 与复盘主键。
- 缺口：未在有 `evidence_ref` 的同 run 下补齐真实 route 复跑产物，因此 O3 仅达到软件复盘层。

### 关键证据

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest ...` -> `13 tests` `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile ...` -> pass
- `docs/navigation/fixed_route_workflow.md` 更新了 `evidence_ref` 对齐检查清单

## 可放行项

- 本轮可作为 O3 run-level 可复现能力的“离线证明闭环”收口。

## 不可放行项

- 未形成上车 route replay 的 run-level 复现证据（同一 `evidence_ref` 的 task_record/route_replay 落盘核验）。
