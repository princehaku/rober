# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - Pre Start

## 状态

- 阶段：pre-start started
- 时间：2026-05-11 06:10 Asia/Shanghai
- 目录：`sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/`
- Owner：`product-okr-owner`
- 本轮目标：把上轮软件端收口后的闭环，继续聚焦 O1/O2/O3 低完成度主线，不偏向 full-stack。

## 本轮启动依据（证据驱动）

1. `OKR.md`（4.1 当前快照）显示 O1/O2/O3 仍约 75~76%，并且都标注“真实 HIL/真实关键路线实机/反馈闭环缺口”。
   - 证据来源：`OKR.md`（O1/O2/O3 当前进度段）。
2. `sprints/2026.05.11_05-06_hil-route-e2e-hardening/tech-done.md` 已完成字段层级落地，但也明确标注“真实 HIL 尚未执行，`pyserial`/上机条件导致阻塞”。
   - 证据来源：`sprints/2026.05.11_05-06_hil-route-e2e-hardening/tech-done.md`（风险与剩余任务）。
3. `sprints/2026.05.10_21-22_review-progress-metrics/final.md` 与 `pre_start.md` 重复出现 `test_*review*py` 命名导致 `NO TESTS RAN`、验证围栏摩擦。若不修复会继续影响验收。 
   - 证据来源：`sprints/2026.05.10_21-22_review-progress-metrics/final.md`。

## O1/O2/O3 低完成度主线

- O1：硬件协议与反馈链路闭环。
  - 建议：先补齐可复现 `hil_pass` 证据入口与 run 元数据，固定 `software_proof`/`hil_pass` 边界。
  - 证据来源：`OKR.md`（O1 75%/缺口）、`05-06 tech-done.md`（runbook 与 HIL 阻塞）、`21-22 review`（验收围栏问题）。

- O2：送垃圾任务失败恢复闭环。
  - 建议：固化任务失败/超时/取消分支的 `failure_code/state_transition_history/human_intervention_required/evidence_ref` 一致归档。
  - 证据来源：`OKR.md`（O2 76%/仍缺真实复现）、`05-06 tech-done.md`（行为链条字段落地）、`21-22 review`（验收命令稳定性）。

- O3：固定路线可复验闭环。
  - 建议：对齐 route 的 `checkpoint/current_index/target/evidence_ref/failure_code` 到任务记录复盘字段。
  - 证据来源：`OKR.md`（O3 76%/关键点闭环未实机）、`05-06 tech-done.md`（fixed-route 字段增强）、`21-22 review`（围栏与回归可执行性）。

## 本轮边界（避免偏离 full-stack）

- 不做：
  - 不新增 elevator assisted 电梯控制能力、楼层识别模型、视觉 detector 扩展。
  - 不扩大测试矩阵。
  - 不把 `software_proof` 伪装成实机通过证据。
  - 不把 full-stack 作为主责闭环入口。
- 只做：
  - O1/O2/O3 的闭环字段与实机证据主线。
  - review 命名导致验收失败的最小修复（可执行命令替代）。

## 关键验收动作（都附证据归属）

1. O1：完成一次可追溯 `hil_pass`（或明确 blocked）并形成 evidence_ref。
   - 证据来源：`OKR.md`（硬件协议实测缺口）、`05-06 tech-done.md`（HIL 运行依赖阻塞）。
2. O2：一次任务失败/取消场景保留完整任务复盘字段。
   - 证据来源：`OKR.md`（任务闭环失败恢复缺口）、`05-06 tech-done.md`（task record 字段落地）。
3. O3：固定路线故障码与 checkpoint 信息可复用一次 run 的 evidence_ref 回放。
   - 证据来源：`OKR.md`（固定路线实机验证缺口）、`05-06 tech-done.md`（route 状态字段更新）。
4. 验收围栏：修正 `NO TESTS RAN` 类风险，保留最小命令，不新增 review 测试文件。
   - 证据来源：`21-22 review`（`NO TESTS RAN`、命名修复需求）。

## 依赖与阻塞

- 依赖：WAVE ROVER 串口上机条件、`docs/vendor/VENDOR_INDEX.md` 约束核对。
- 阻塞：上机条件不足时，O1 产出可能停留在软件可复现证据，不可上升到实机通过。
- 接口风险：`evidence_ref` 命名规则不一致将导致 O1/O2/O3 复盘失真。
