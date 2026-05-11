# Sprint 2026.05.11 07-08 HIL proof and route replay - Pre Start

## 状态

- 阶段：pre-start completed
- 时间：2026-05-11 11:20 Asia/Shanghai
- 目录：`sprints/2026.05.11_07-08_hil-proof-and-route-replay/`
- Owner：`product-okr-owner`
- 本轮目标：对齐 06-07 收口结论，将 OKR 低完成度主线（O1/O3）推进到实机证据面，避免再次把软证据误当 HIL 完成度。

## 阶段收口

- pre-start 输入已被 PRD/Tech Plan/Tech Done/Side2Side/Final 全链路消费。
- 本阶段按“已启动并已完成交接”收口，不新增范围。

## 启动依据（证据驱动）

1. `OKR.md` 4.1 仍显示 O1/O2/O3 约 75%~76%，且明确缺少真实 `hil_pass` 与固定路线实跑复盘。
   - 证据来源：`OKR.md:~4.1`
2. `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/tech-done.md` 与 `/side2side_check.md` 复核结果：
   - O1 本轮仍缺实机 `hil_pass` evidence packet（`command.txt`、`serial.log`、`feedback_T1001.log`）。
   - O3 本轮未新增 route 实跑证据。
   - 06-07 收口已建议新起 sprint。 
   - 证据来源：`sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/tech-done.md`, `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/side2side_check.md`
3. `sprints/2026.05.10_21-22_review-progress-metrics/final.md` 重复指出 `test_*review*py` 命名导致 `NO TESTS RAN`，下一轮应直接用最小可执行命令闭环围栏。
   - 证据来源：`sprints/2026.05.10_21-22_review-progress-metrics/final.md`

## 本轮聚焦（低完成度主线）

- O1：补齐一次可追溯的 `hil_pass` run。
  - 目标证据：固定 `evidence_ref` 串联：`hardware smoke`、`T1001 feedback`、`/odom`、`/imu/data`、`/battery`、task record。
  - 输出约束：`source=software_proof` 与 `source=hil_pass` 分离。

- O3：补齐一次固定路线复现（route replay）实证。
  - 目标证据：同一 run 的 `route_progress.checkpoint/current_index/target/failure_code/evidence_ref` 与 task record 复盘字段一致。

- O2：本轮不展开新功能，仅修补 O2 复盘完整性缺口。
  - 输出约束：用本轮 O1/O3 的同一 `evidence_ref` 补齐失败场景字段复现，不重复打散文档结构。

## 边界（按优先级收口）

- 不做：`elevator_assist`、视觉 detector 扩展、OCR、硬件新型号接入。
- 不做：新增测试文件。
- 不做：把 `software_proof` 等同于 `hil_pass`。

- 做：
  - 新增 `scripts/hardware_smoke_wave_rover.py` 的 `hil_pass` run 与 evidence 落盘。
  - 从 fixed-route 到 task_record 的复现链路一次性打通。
  - 调整验收围栏命名策略，消除 `NO TESTS RAN`。

## 本轮关键验收目标

1. 产出一次完整 `hil_pass` evidence packet（含 run-level `evidence_ref`）。
2. 产出一次 route replay 的实测复盘证据，包含失败码或成功码与复盘字段。
3. 复用本轮 evidence_ref 打通 `task_orchestrator/task_record/operator diagnostics/fixed_route`。
4. 验收命令覆盖 `hil_pass` 与 route 复现，不新增 review 测试文件。

## 风险与阻塞

- 上机串口与依赖（pyserial）不到位会导致 O1 阻塞，需要在 `wave_rover_hil_evidence.md` 中记录 `blocked`。
- 路线实跑时若固定路线文件/关键帧不一致导致中断，需要把 `checkpoint_id`、`failure_code` 与 `evidence_ref` 一并归档，避免复盘失真。
