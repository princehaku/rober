# Sprint 2026.05.11 05-06 HIL + Route E2E Hardening - PRD

## 用户价值与产品北极星

北极星是“普通手机用户也能完成一次可复盘、可恢复、可解释的送垃圾任务”。

本轮价值边界：从“软件 dry-run 看上去可用”提升到“实机可复现、可追溯、可判定的交付闭环”，并把失败时对普通用户的指导准确化。

## 目标与验收意图

把 `Objective 1/2/3` 从 dry-run 软件证据推入实机证据链路，确保每次任务可在一次失败/成功复现实验中被追踪。

验收核心：同一场实机任务，`task record`、`navigation state`、`operator diagnostics` 三端读取同一 `evidence_ref`，并能区分 `source`。

## OKR 映射（本轮）

- Objective 1：硬件协议可信底盘
  - KR1：把 WAVE ROVER HIL 的关键参数（设备/波特率/反馈字段）与结果记录化为可追溯样例。
  - KR2：`/feedback` 与里程反馈字段在证据中写明来源与采样区间。
  - KR3：`software_proof` 与 `hil_pass` 通过统一字段分层，不互相替代。
- Objective 2：送垃圾任务闭环
  - KR1：补齐真实送达流程失败恢复状态与错误码。
  - KR2：任务记录保留失败分支和人工接管建议，不能 silent-success。
  - KR3：`DELIVERING -> DROPOFF -> RETURNING -> IDLE/ERROR` 全链路可回放。
- Objective 3：可验证导航与固定路线
  - KR1：fixed-route 检查点与任务复盘字段对齐。
  - KR2：路线缺失/关键点偏差/导航中断有可复现证据。
  - KR3：支持 dry-run 与 hil 的证据分层显示。

## 本轮要做 / 不做

### 要做

1. 优先推进 O1：先完成实机 HIL 入口、反馈样本与命名规范。
2. 接着推进 O2：补齐任务失败恢复与复盘字段。
3. 再推进 O3：固定路线与状态字段一致性。
4. 评审围栏最小修复：消除本轮 review 命名导致的 `NO TESTS RAN` 风险。

### 不做

- 不做真实电梯开门/按键控制能力，不做楼层 OCR 真机闭环。
- 不扩大视觉 detector 或大规模回归矩阵。
- 不把任何 dry-run 证据改写为 HIL 通过。

## 优先级与验收口径

- P0（优先级最高）：O1 硬件 HIL 证据分层与样本留存。
- P1：O2 任务失败恢复与复盘。
- P2：O3 固定路线复盘字段与一致性。
- P3：`review` 命名与 `README` whitespace 清理（降低验收摩擦）。

验收标准：
1. 实机失败/成功都能写入 `source=hIL_pass` 任务证据，且存在可复现 run 目录。
2. `result_path` 与 `state_transition_history` 在失败和成功路径均有。
3. `operator/diagnostics` 能展示 evidence 来源、证据链接与建议处理动作。
4. 复核命令在本轮可重复执行且无 `NO TESTS RAN`。

## 对应责任 Engineer

- `hardware-engineer`：O1 证据入口、HIL 参数、反馈采样、硬件文档。
- `robot-software-engineer`：O2 任务状态机失败恢复与记录字段。
- `autonomy-engineer`：O3 route 固定路线状态字段对齐。
- `full-stack-software-engineer`：O1/O2/O3 证据源与复盘信息可视化。
