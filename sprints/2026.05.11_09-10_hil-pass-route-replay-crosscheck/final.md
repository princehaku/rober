# Sprint 2026.05.11 09-10 HIL pass and route replay crosscheck - Final

## 状态

- 阶段：final draft
- 时间：2026-05-11 16:47 Asia/Shanghai
- Owner：`autonomy-engineer`
- 结论：软件复盘闭环通过；硬件 run-level 复核仍待补

## 本轮结论

- O3 fixed-route 软件复盘对齐方向已推进：route 状态字段按 `evidence_ref` 统一复用。
- 已补齐只读对账脚本 `scripts/evidence_crosscheck.py`，用于 status/replay 与 task_record 的 run-level 回放一致性核验。
- 真机 `hil_pass` 样本尚未形成（环境约束），O3 本轮以软件复现为主，复盘脚本可用于补齐后复验。

## 风险与阻塞

- 无真实运行样本时，task_record 侧 route_progress 对账依赖 `nav_result.evidence` 兜底，缺字段会显示为可追踪差异而非失败吞掉。
- 缺少同一 run 的真实 task_record 文件，`evidence_ref` 联动仍需上机回放完成后补齐。

## 下一步

1. 在有硬件条件下，固定一轮 `evidence_ref` 并同时记录：
   - fixed-route status JSON
   - route replay jsonl
   - task_record JSON
2. 用 `python3 scripts/evidence_crosscheck.py <status> --task-record <task_record> --evidence-ref <same_ref>` 验证字段闭环。
3. 若 task_record 对账仍有差异，按行为端 contract 补齐 `route_progress` 写入路径。
