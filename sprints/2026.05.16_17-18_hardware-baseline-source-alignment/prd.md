# Sprint 2026.05.16_17-18 Hardware Baseline Source Alignment - PRD

sprint_type: epic

## 1. 用户价值

普通用户最终只看到“这台车该有什么硬件、缺什么材料、下一步谁补证据”。如果默认硬件集、传感器目标基线和 vendor 来源边界互相矛盾，后续采购、装机、bringup、手机状态解释都会把同一缺口说成不同版本，导致现场无法推进。

本轮把 PR #5 的评审风险固化为可执行 source-alignment gate，让 Hardware / Robot / Mobile 对同一硬件基线状态给出一致的、可追溯的、fail-closed 摘要。

## 2. OKR 映射

- Objective 1：硬件协议可信底盘。通过 vendor/source alignment 约束硬件事实来源，减少未证实传感器假设进入 bringup 和 HIL 计划。
- Objective 4：手机用户体验与低成本量产边界。让手机端能只读展示“默认硬件集 / 目标传感器基线 / vendor coverage / 缺失材料”一致摘要，避免普通用户或现场支持误判。
- Objective 5：不推进。当前仍缺真实外部云/4G/OSS/CDN/DB/queue 证据。

## 3. 范围

本轮做：

- 新增 `hardware_baseline_source_alignment` PC gate，读取 `docs/product/production_hardware_boundary.md` 与 `docs/vendor/VENDOR_INDEX.md`，输出 artifact / summary。
- Robot diagnostics 以 metadata-only 方式消费该 summary，缺失、unsupported、unsafe 或 success/control 文案均 fail closed。
- mobile/web 新增只读 panel，展示 source-alignment status、default hardware set、target baseline、vendor coverage、missing evidence 和 control boundary。
- 更新相关 `docs/product/`、`docs/interfaces/`、sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。

本轮不做：

- 不采购、不安装、不接线、不标定 2D LiDAR / ToF。
- 不打开真实串口、WAVE ROVER、Orange Pi UART、ROS graph 或 Nav2 runtime。
- 不证明真实 HIL、真实手机、真实路线、电梯、投放、取消或 delivery success。
- 不推进 Objective 5 外部云证据。

## 4. 验收口径

用户能在 PC gate、Robot diagnostics 和 mobile/web 中看到同一 source-alignment 状态：

- 默认硬件集与目标传感器基线不互相冒充。
- `docs/vendor/VENDOR_INDEX.md` 被明确列为 source boundary。
- 2D LiDAR / ToF 仍是 procurement/source/material pending，不是已安装硬件。
- 所有输出继续 fail closed：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
