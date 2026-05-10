# Sprint 2026.05.11 01-02 Hardware Proof Param Gate - Pre Start

## 状态

- 阶段：pre_start completed。
- 时间：2026-05-11 01:12 Asia/Shanghai。
- Product Owner：`product-okr-owner`（由主会话代行拆解）。
- Sprint：`sprints/2026.05.11_01-02_hardware-proof-param-gate/`。
- 实现 owner：`robot-software-engineer`（单线闭环）。

## 用户目标

继续推进 OKR 低完成度部分，优先补 Objective 1 的功能缺口：让 operator gateway 通过 launch 参数接入 `hardware_proof_ref`，使 `/api/diagnostics.hardware_proof` 可以读取硬件 software-proof 产物，不再固定停在“未配置”。

## OKR 映射

- 主目标：Objective 1（当前约 74%）
  - KR1/KR5：把诊断链路中的硬件 proof 配置入口参数化并通过 bringup/autonomous 透传。
- 次目标：Objective 5（当前约 79%）
  - KR4：远程诊断包更可用，手机支持链路可直接看到配置后的 hardware proof 摘要。

## 本轮做什么

1. 为 `operator_gateway` 增加 `hardware_proof_ref` ROS 参数读取与 diagnostics 透传。
2. 在 `bringup.launch.py` / `autonomous.launch.py` 增加 operator gateway 的 hardware proof launch 参数，并映射到 node 参数。
3. 补齐 behavior static test 与 bringup launch contract test 护栏。
4. 同步接口文档和 OKR/sprint 留档。

## 本轮不做什么

- 不做 WAVE ROVER 实机/HIL。
- 不改硬件驱动协议实现，不改底盘速度映射。
- 不做跨模块重构。

## 风险与边界

- 本轮只提升“配置入口 + 软件诊断可用性”，不代表硬件已通过 HIL。
- `hardware_proof_ref` 默认值保持保守，不伪造硬件通过结论。
