# Sprint 2026.05.11_09-10_hil-pass-route-replay-crosscheck PRD

## 产品目标

把 `sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck` 的交付链条从“已有技术结果”修复为“可持续执行链条”：  
在不新增本轮功能边界的前提下，用可追溯的优先级（O1→O2→O3）明确验收条件、失败边界和 evidence 责任。

一句话：先讲清楚什么是 `software_proof`，什么是 `hil_pass`，再把 `route_progress` 与 `task_record` 的 `evidence_ref` 对账定义为下一步执行入口。

## 文档阶段门禁

- 前置文档：`pre_start.md`。
- 当前阶段：`prd.md`。
- 阶段完成条件：OKR 映射、范围、验收顺序（O1→O2→O3）、阻塞与责任边界清晰可执行。
- 下一阶段：仅在本阶段完成后允许进入 `tech-plan.md`。

## OKR 映射（严格 O1 → O2 → O3）

| 优先级 | OKR | 本轮映射 |
| --- | --- | --- |
| O1（第一优先） | Objective 1：硬件协议可信底盘控制层 | 本轮确认边界：保持 `hil_pass` blocked，保留 `software_proof` 与上车前 `hil_pass` 检查清单，不将实机闭环提前宣告 |
| O2（第二优先） | Objective 2：可恢复送垃圾任务闭环 | 本轮确认任务记录失败路径边界：`failure_code`/`human_intervention_required`/`state_transition_history` 不可用时禁止进入 `closed`；`task_record` 与 `state machine` 仅能标注为可复核缺口 |
| O3（第三优先） | Objective 3：可验证导航与固定路线 | 本轮固定路线验收聚焦 `evidence_ref` 对账与 dry-run 软件一致性，明确与 O1/O2 的 run-level gap |

## 范围内

- 补齐 `pre_start.md`、`prd.md`、`tech-plan.md` 及其 `O1→O2→O3` 证据优先级。
- 将本 sprint 当前状态明示为：
  - O1：`hil_pass` 不足（blocked）
  - O2：`task record` 与任务失败恢复复盘缺口
  - O3：`route_progress` 软件对账完成，run-level 真机复盘未完成
- 定义验收口径顺序与文档链路：不能以 O3 或 P1 结果替代 O1 blocked 解锁。
- 明确本轮仅文档与验收边界收口，后续执行仍走软件/硬件对应的下一轮实现。

## 范围外

- 不新增固定路线算法、Nav2 策略、视觉、声音、HIL 控制算法。
- 不进行代码层新功能开发与修复（本轮职责仅闭环文档与证据口径）。
- 不承诺新增真实 `hil_pass` 产物：`command.txt`、`serial.log`、`feedback_T1001.log` 缺失时不变更 `OKR` 状态为通过。

## 用户价值

1. 研发/维护者能知道“为什么没 close”而不是看到误导性完成文案。
2. 下一轮执行者能明确下一步输入：先补 O1 设备样本，再补 O2 失败复盘，再补 O3 run-level 串联。
3. CEO/PM 可在 `side2side/final` 看到 O1→O2→O3 的闭环顺序，不被单点验收误导。

## 验收口径（绑定顺序）

1. O1：`hardware` 真实样本不足时，标记为 `hil_pass blocked`，并在文档中保留 vendor 与命令来源约束。
2. O2：`task record` 与 `state transition` 的失败恢复证据不能缺位；无 run-level 证明时为 `partial` 或 `blocked`。
3. O3：`route_progress`、`checkpoint/current_index/target/failure_code/evidence_ref` 在 `software` 侧通过对账可运行；real run-level 串联仍为后续待补。
4. O1→O2→O3 顺序必须在文档中明确，任何阶段性复盘不得跳过前序说明。
5. `pre_start/prd/tech-plan` 三文档全部存在且可读，且均可追溯到本 sprint 的 `tech-done/side2side/final`。

## 依赖与失败处理

- 文档成功依赖：本轮上下文留档完整存在（`final.md`、`tech-done.md`、`side2side_check.md`）。
- 真实执行依赖：WAVE ROVER 串口 `/dev/ttyUSB0` 可访问、可写 `evidence` 文件目录。
- 失败处理：若缺 `hil_pass` 真实样本或 task_record 真机样本，本轮不升级为 O1/O2 完成，改为 `blocked`/`partial` 并留在下一轮执行卡项。
- 证据边界：所有对齐日志默认标记 `software_proof`，除实机上车后证据确认不得称为 `hil_pass`。

## 本文件 Gate

- PRD 已定义本轮范围、顺序（O1→O2→O3）与边界，允许进入 `tech-plan.md`。
