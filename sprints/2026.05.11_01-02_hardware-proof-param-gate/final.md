# Sprint 2026.05.11 01-02 Hardware Proof Param Gate - Final

## 本轮结论

本轮完成 Objective 1 的一个低成本但关键补洞：把 operator gateway 的 `hardware_proof_ref` 从“诊断函数内部可用”推进为“launch 可配置并可透传到 `/api/diagnostics.hardware_proof`”。

新增能力：
- 运维/调试可以在 `bringup.launch.py` 或 `autonomous.launch.py` 通过 `operator_hardware_proof_ref` 指定 software-proof 产物路径。
- operator gateway 在不改代码的情况下读取该路径并进入 diagnostics payload。

## OKR 影响

- Objective 1 从约 74% 调整到约 75%。
- 贡献类型：软件证据链完整性提升（参数可配置 -> node 参数 -> diagnostics payload），不是硬件实机能力提升。

## 验证证据

- behavior operator targeted tests：`Ran 48 tests ... OK`
- bringup launch contract tests：`Ran 9 tests ... OK`
- changed python files `py_compile`：通过
- full smoke：分组 `6/24/44/9/128/13 tests` 全部 `OK`
- `git diff --check`：通过（无 whitespace 错误）

## 残留风险与下一步

1. 仍缺真实 WAVE ROVER HIL；software proof 不能替代 UART/运动/IMU/电池实测。
2. 推荐下一轮由 Hardware owner 在实机环境提供 `hardware_proof_ref` 实际产物路径样例与上车证据，补齐 Objective 1 的 HIL 缺口。
