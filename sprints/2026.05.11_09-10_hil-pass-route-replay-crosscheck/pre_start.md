# Sprint 2026.05.11_09-10_hil-pass-route-replay-crosscheck Pre Start

## 轮次定位

本轮主题：补齐阶段文档链路并对齐 O1→O2→O3 的验收优先级，使本轮交付可直接进入执行，不新增本 sprint 外功能承诺。

本轮不是再新增功能，只做可执行交付驱动：
1) 明确硬件与软件证据边界（O1）；
2) 明确任务复盘可复现性与失败恢复证据边界（O2）；
3) 以证据可对账为导向闭环 O3 fixed-route replay（O3）。

## 已读依据

- `AGENTS.md`
- `OKR.md`
- `/Users/m4/apps/rober/sprints/2026.05.11_07-08_hil-proof-and-route-replay/final.md`
- `/Users/m4/apps/rober/sprints/2026.05.11_08-09_hil-pass-and-route-replay/final.md`
- `/Users/m4/apps/rober/sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/final.md`
- `/Users/m4/apps/rober/sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/tech-done.md`
- `/Users/m4/apps/rober/sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/side2side_check.md`
- `/Users/m4/apps/rober/docs/navigation/fixed_route_workflow.md`

## CEO 口径（本轮不允许扩）

1. 上轮 `O3` 软件侧复核通过，`hil_pass` 回放闭环仍缺失时，保持 `hil_pass` 状态为 blocked，不可升级到实机完成。
2. 本轮只做阶段文档修复+验收边界对齐，不新增底层硬件/路径策略重构，不新增测试面。
3. 本轮验收顺序严格为 O1→O2→O3，未满足前序不得在 `side2side/final` 写 `closed`。
4. 任何 `evidence_ref` 对账都必须标注 `software_proof` 与 `hil_pass` 的边界，不可混淆。

## 上轮遗留与阻塞

| 类型 | 事项 | 本轮处置 |
| --- | --- | --- |
| 遗留 | 真实 `O1` `hil_pass` run-level 样本缺失（`command.txt`/`serial.log`/`feedback_T1001.log`） | 本轮不补采样；更新文档将其固定为 blocked 证据边界 |
| 遗留 | O2 送垃圾任务失败/超时/取消 run-level 统一复盘缺失 | PRD/tech-plan 明确为本轮前置边界与执行顺序，待下轮接续 |
| 遗留 | O3 `route_progress` 同一 run-level 对账仅软件离线成功，尚无真机 route replay 与 task_record 串联 | 将本轮目标定为“证据口径可执行化 + 真实 run-level 前置条件收口” |
| 风险 | `sprints/2026.05.11_09-10...` 现有 `tech-done/side2side/final` 仅为草稿链路，缺少 `pre_start/prd/tech-plan` 正式 gate | 本文件先补齐前序文档并定义验收边界 |

## 本轮组织链路

CEO -> Product Manager / OKR Owner -> Engineers

| 角色 | 本轮任务 |
| --- | --- |
| `product-okr-owner` | 本轮三份阶段文档完整化、验收口径排序与边界锁定（O1→O2→O3） |
| `robot-software-engineer` | 在执行阶段同步确认 O2 任务失败/超时/取消与 task_record 对账范围 |
| `autonomy-engineer` | 对齐 O3 `route_progress` 与 `evidence_ref` 对账规则，明确 software 与 hil gap |
| `hardware-engineer` | 锁定 O1 `hil_pass` 缺口、样本字段与上机证据清单 |
| `full-stack-software-engineer` | 锁定手机/接口侧状态字段是否足够判定 final 状态 |

## P0/P1 风险

| 等级 | 风险 | Gate |
| --- | --- | --- |
| P0 | 把 O3 软件对账结果误认作 O1 `hil_pass` 完成 | 仅在 `docs` 标注 `software_proof` 与 `hil_pass` 边界 |
| P0 | 未按 O1→O2→O3 顺序定义验收口径，导致 side2side/final 判定失真 | PRD 明确验收顺序与依赖 |
| P1 | 本轮后续执行仍无阶段化文档，可追责链路断裂 | `tech-plan.md` 必须提供可执行验收动作与交付门控 |

## 本文件 Gate

- 证据边界和优先级已经按 O1→O2→O3 定义，允许进入 `prd.md`。
- `pre_start`、`prd`、`tech-plan` 均与现有 `tech-done/side2side/final` 的内容兼容，不新增本 sprint 外任务承诺。
