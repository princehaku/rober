# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - Pre Start

## 状态

- 阶段：pre-start
- 时间：2026-05-11
- 目录：`sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/`
- Owner：`full-stack-software-engineer`
- 本轮目标：为 O1/O2/O3 的新证据字段与故障码，补齐 operator gateway 统一透传链路，并在手机端给出可执行恢复建议。

## 证据驱动启动依据

- O1/O2/O3 已有部分证据字段在行为侧已有落盘，但 operator status/diagnostics 透传口径分散，存在重复拼接与字段丢失。
- `failure_code/evidence_ref/source/state_transition_history/human_intervention_required` 在多入口（`latest_status`、`task_record`、`last_task`）提取逻辑不统一，容易出现 UI 与后端契约偏差。
- 现有手机端只给“人工接管”提示，无法把失败分支映射为下一步可执行动作，用户无法快速恢复。

## 本轮执行清单（仅本轮交付）

1. 在 operator gateway 行为层统一 `failure_code/evidence_ref/source/state_transition_history/human_intervention_required` 的透传规则，避免重复拼接。
2. 保持 `status` 与 `diagnostics` 在 payload 上下文中一致透传，避免 O1/O2/O3 证据信息在链路中断层。
3. 在 operator 页面展示新增字段，并基于现有 evidence 与失败分支给出可执行恢复建议。
4. 在 sprint 文档写清验收边界与残留风险，不新增测试文件。

## 交付范围（本轮）

- `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/pre_start.md`
- `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/prd.md`
- `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/tech-plan.md`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`

## 验收边界（本轮）

- 本轮只补强 O1/O2/O3 证据透传一致性与用户提示，不涉及硬件协议、UART/串口、ESP32/Orange Pi 供应商细节。
- 不新增新测试文件；沿用现有 `operator_gateway` 相关单测。
- 不改行为状态机策略与任务调度算法。
