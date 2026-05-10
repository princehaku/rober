# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - PRD

## 用户价值与北极星

把“普通手机用户一键发起送垃圾任务”从演示可用提升到“可复现、可恢复、可解释”的实机可交付闭环：同一趟任务能由证据说明是否真正送达、为何失败、如何恢复。

## 本轮目标（仅 O1/O2/O3）

1. 将上轮软件侧改造（O1/O2/O3）持续推进到可复现证据主线，不将 full-stack 展示作为验收主目标。
   - 证据来源：`OKR.md`（O1/O2/O3 低完成度）、`05-06 tech-done.md`（O1/O2/O3 已有软件字段）、`21-22 review`（验收命令仍有摩擦）。
2. 统一 O1/O2/O3 证据字段与复盘口径，优先解决“实机闭环不足”和“失败不可恢复”问题。
   - 证据来源：同上。
3. 保持围栏最小，不新增 test 文件。
   - 证据来源：`OKR.md` 进度复盘中强调真实证据优先于广义回归，`21-22 review` 重复暴露命名风险。

## OKR 映射（本轮下沉）

### Objective 1：硬件协议与反馈源可信

- KR1：形成一次可复现的 WAVE ROVER 运行证据（参数、反馈字段、`evidence_ref`）。
  - 证据来源：`OKR.md`（真实 WAVE ROVER HIL缺口）、`05-06 tech-done.md`（HIL 运行模板与阻塞信息）。
- KR2：明确 `hil_pass` 与 `software_proof` 分层边界。
  - 证据来源：`OKR.md`、`05-06 tech-done.md`。
- KR3：在任务复盘中可回看硬件样本来源。
  - 证据来源：`05-06 tech-done.md`（hardware diagnostics 文档链条）。

### Objective 2：送垃圾任务闭环可恢复

- KR1：送达任务失败、超时、取消链路产生完整 `failure_code` 与 `state_transition_history`。
  - 证据来源：`OKR.md`（任务闭环缺口）、`05-06 tech-done.md`（task record 字段能力）。
- KR2：失败场景提供可执行干预建议，并写入 `human_intervention_required`。
  - 证据来源：`OKR.md`（需可复苏）、`05-06 tech-done.md`。
- KR3：任务复盘与 diagnostics/状态端对齐同一 `evidence_ref`。
  - 证据来源：`05-06 tech-done.md`（多端字段统一趋势）、`21-22 review`（验收链路一致性问题）。

### Objective 3：固定路线可验证

- KR1：固定路线 `checkpoint/current_index/target` 与任务复盘字段对齐。
  - 证据来源：`OKR.md`（路测/固定路线实测缺口）、`05-06 tech-done.md`（fixed-route 字段增强）。
- KR2：路线中断/缺点/失败码可复现归因。
  - 证据来源：同上。
- KR3：dry-run 与 hil_pass 证据类型可分离展示。
  - 证据来源：`OKR.md`（不能将软件证据视为实测）、`05-06 tech-done.md`（来源分层尝试）。

## 本轮范围：做 / 不做

### 做什么（仅 O1/O2/O3）

1. O1：先补硬件 HIL 证据执行链与 run 分层。
   - 证据来源：`OKR.md`、`05-06 tech-done.md`。
2. O2：再补任务失败恢复与 evidence_ref 回放一致。
   - 证据来源：`OKR.md`、`05-06 tech-done.md`。
3. O3：再补 fixed-route 字段对齐与复盘一致。
   - 证据来源：`OKR.md`、`05-06 tech-done.md`。
4. 收口 `review` 命名问题，防止 `NO TESTS RAN`。
   - 证据来源：`21-22 review`。

### 不做

- 不做：新增电梯控制、OCR、楼宇模型、视觉检测训练矩阵。
- 不做：新增测试文件；不扩展 full-stack 作为主线。
- 不做：把 `software_proof` 标记为 `hil_pass`。

## 优先级

- P0（主线）：O1（HIL 证据分层与可复现）
- P1：O2（失败恢复与复盘字段）
- P2：O3（固定路线可复验字段对齐）
- P3：review 围栏修复（避免 `NO TESTS RAN`）

## 验收口径

1. O1 有至少一次 `hil_pass` 或明确 blocked 记录（含参数、时间戳、`evidence_ref`）。
   - 证据来源：`OKR.md`、`05-06 tech-done.md`。
2. O2 失败/超时/取消路径 `failure_code`、`state_transition_history`、`human_intervention_required` 全链路存在。
   - 证据来源：`OKR.md`、`05-06 tech-done.md`。
3. O3 fixed-route 的 checkpoint/index/target 能与任务复盘 run 对齐。
   - 证据来源：`OKR.md`、`05-06 tech-done.md`。
4. 回归命令可执行且不新增测试文件。
   - 证据来源：`21-22 review`（命名造成 NO TESTS RAN）。

## 对应责任 Engineer

- 主责：
  - `hardware-engineer`（O1）
  - `robot-software-engineer`（O2）
  - `autonomy-engineer`（O3）
- 同步：`full-stack-software-engineer`（仅同步消费，不承担主线闭环）
  - 证据来源：`OKR.md`（主线是 O1/O2/O3）与 `05-06 tech-done.md`（当前已完成 O1/O2/O3 软件侧闭环部分）。
