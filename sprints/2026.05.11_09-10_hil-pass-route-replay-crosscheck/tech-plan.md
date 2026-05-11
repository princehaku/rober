# Sprint 2026.05.11_09-10_hil-pass-route-replay-crosscheck Tech Plan

## 文档阶段门禁

- 前置文档：`prd.md`。
- 前置 gate：PRD 已明确本轮范围、验收顺序（O1→O2→O3）与 evidence 边界。
- 当前阶段：TECH PLAN。
- 本阶段完成条件：三方可执行范围清晰、验收命令可复用、失败边界可复核。
- 下一阶段：技术执行与验收完成后进入 `tech-done.md`。

## 总体技术方案

1. 用三文档链路将 `software_proof` 与 `hil_pass` 从口径上解耦：不把同一跑数缺失的软对账当实机闭环。
2. 在本 sprint 约束下，优先完成 O1→O2→O3 的执行顺序记录和验收入口，形成下一轮工程的交付脚手架。
3. 明确各 Owner 在每个优先级下的责任边界：谁补哪个缺口、缺口未补时如何归类。
4. 使用轻量验证命令先验阶段文档存在性和关键词一致性，避免下一轮直接进入执行层时丢失上下文。

## 执行拆分（按优先级）

### O1（第一优先）：硬件与实机闭环边界

- Owner：`hardware-engineer`
- 任务边界：
  - 在 `prd.md`/`pre_start.md` 明确 hil-pass 与软件证据边界后，给出下一轮“硬件可复验”最小清单。
  - 不生成新的 HIL 样本文件，只做文档与下一步执行准入定义。
- 风险：
  - 无串口环境（如 `/dev/ttyUSB0`）将继续阻塞 O1。

### O2（第二优先）：任务复盘与失败恢复证据

- Owner：`robot-software-engineer` 与 `full-stack-software-engineer`
- 任务边界：
  - 对齐 `task_record`、失败恢复字段与消费者可读终态（failure 与 recovery 所需字段）。
  - 明确当 run-level 样本缺失时，`failure_code` 与 `state_transition_history` 的处理策略（partial/blocked）。
- 风险：
  - 无真实 run-level 任务样本时，部分路径仍仅能以 `software_proof` 维持观察而非通过。

### O3（第三优先）：固定路线 run-level 对账

- Owner：`autonomy-engineer`
- 任务边界：
  - 固化 `checkpoint/current_index/target/failure_code/evidence_ref` 为 O3 端到端核验最低字段集合。
  - 对齐 `fixed-route status`、`route replay`、`task_record` 的术语与证据口径，保留 dry-run 已通过状态。
- 风险：
  - 若没有同一 `evidence_ref` 的真实 run-level 样本，`route replay` 与任务闭环保持 `software_proof` 状态，不得标为 `hil_pass`。

## 具体交付清单（当前 sprint 目标）

- `sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/pre_start.md`
  - 已补齐上轮遗留、阻塞、P0 风险、owner 与 O1→O2→O3 优先级。
- `sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/prd.md`
  - 已补齐范围、OKR 映射、验收顺序与证据边界。
- `sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/tech-plan.md`
  - 已补齐执行分解与验收命令。
- `OKR.md`
  - 明确 O1→O2→O3 本轮优先级与 evidence 边界（software vs hil）。

## 验证命令（本阶段门禁）

| 层级 | 命令 | 预期 |
| --- | --- | --- |
| 文档存在 | `test -f sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/pre_start.md` | 存在并退出码 0 |
| 文档存在 | `test -f sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/prd.md` | 存在并退出码 0 |
| 文档存在 | `test -f sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/tech-plan.md` | 存在并退出码 0 |
| 关键内容 | `rg -n "O1|O2|O3|hil_pass|software_proof|evidence_ref|验收|优先级|阻塞|责任" sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/{pre_start.md,prd.md,tech-plan.md}` | 文档包含 O1/O2/O3、证据边界、验收和责任 |

## 风险边界

- 本轮没有产生新的代码提交与实机样本；任何 `route replay` 或 `task_record` 成果仅能用于 `software_proof` 范围。
- 本轮文档链路不构成 `hil_pass`，真实 `evidence_pass` 仍依赖下一轮上机样本。
- 下轮应继续禁止跳过 O1 阶段直接进入 O2/O3 的 `closed` 结论。

## 本文件 Gate

- `tech-plan.md` 已明确优先级顺序、责任分工、验收命令与失败边界。
- 允许进入执行阶段并继续 `tech-done.md` 更新。
