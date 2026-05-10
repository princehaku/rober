# Sprint 2026.05.11 01-02 Hardware Proof Param Gate - PRD

## 状态

- 阶段：prd completed。
- 时间：2026-05-11 01:12 Asia/Shanghai。
- 实现 owner：`robot-software-engineer`。

## 背景

`OKR.md` 当前最低完成度之一是 Objective 1（约 74%）。现有 `/api/diagnostics` 已支持 `hardware_proof` 摘要，但 operator gateway 运行参数链路尚未提供 `hardware_proof_ref`，导致默认常见场景只能返回未配置/读不到文件，影响远程诊断实用性。

## 需求

1. `operator_gateway` 支持 `hardware_proof_ref` 参数声明、读取和 `build_diagnostics_payload()` 透传。
2. `bringup.launch.py` 与 `autonomous.launch.py` 提供 `operator_hardware_proof_ref` launch 参数，并映射到 operator gateway node。
3. static contract tests 覆盖上述参数存在与映射关系。
4. 文档更新：接口文档明确该参数含义与边界（software proof != HIL pass）。

## 验收口径

- 代码层：behavior + bringup 参数链路完整。
- 护栏层：operator tests + launch contract tests + smoke + diff-check 通过。
- 风险口径：明确仍未完成 HIL，不夸大硬件能力。
