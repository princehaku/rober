# Sprint 2026.05.11 01-02 Hardware Proof Param Gate - Side2Side Check

## 对照目标

目标：补齐 operator gateway `hardware_proof_ref` 参数链路，使 `/api/diagnostics.hardware_proof` 可通过 launch 参数读取 software-proof 产物。

## 逐项对照

1. `operator_gateway.py` 声明并读取 `hardware_proof_ref`，并在 diagnostics 透传。
- 状态：完成。
- 证据：参数声明 + `self.hardware_proof_ref` 读取 + `build_diagnostics_payload(... hardware_proof_ref=...)`。

2. `bringup.launch.py` 与 `autonomous.launch.py` 新增 `operator_hardware_proof_ref` 并映射。
- 状态：完成。
- 证据：两份 launch 均新增参数声明，并在 operator gateway node 参数中映射到 `hardware_proof_ref`。

3. behavior static tests 与 bringup launch contract tests 覆盖参数声明和透传。
- 状态：完成。
- 证据：`test_operator_gateway_static.py`、`test_launch_contract_static.py` 新增断言；两套测试均通过。

4. `docs/interfaces/ros_contracts.md` 更新参数入口和边界。
- 状态：完成。
- 证据：Operator Gateway 参数表新增 `hardware_proof_ref`，明确 software proof != HIL。

5. `OKR.md` 当前快照最小范围更新。
- 状态：完成。
- 证据：仅在「4.1 当前 OKR 进度快照」Objective 1 行更新本轮证据与进度。

6. sprint 文档补齐 `tech-done.md`、`side2side_check.md`、`final.md`。
- 状态：进行中（本文件已写；`final.md` 同轮更新）。

## 验证结论

- 验收命令 1/2/3/4/5 已执行通过。
- 本轮属于参数链路闭环，未引入硬件协议新假设。

## 未覆盖项

- 未做真实 WAVE ROVER HIL、UART 实测、轮向/速度单位/IMU/电池上车验证。
- 本轮新增链路只改善 software proof 的可配置性与可消费性，不代表实机能力新增。
