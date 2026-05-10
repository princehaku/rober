# Sprint 2026.05.10 18-19 Hardware Diagnostics Proof - Final

## 状态

- 阶段：final completed。
- 时间：2026-05-10 18:49 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`hardware-engineer`。
- 收口结论：本 sprint 达成软件侧 Objective 1 证据推进；真实 HIL 和 Docker/Humble 仍是后续缺口。

## 用户价值和产品北极星

本轮把硬件桥从“测试散落在代码里”推进为“可离线生成、可复盘、可被后续诊断消费”的 proof artifact。普通用户不会直接看到 UART 或 JSON，但未来手机/售后诊断可以把底盘状态解释成：软件证据完整、配置错误、反馈样例解析失败、需要上车验证。

产品北极星仍是低成本自主垃圾投递机器人。底盘协议可信是手机一键发车之前的地基，本轮没有扩展机械能力或手机 UI，而是把 WAVE ROVER 控制层的可解释性和下一步 HIL 入口补齐。

## OKR 进度变化

- Objective 1：约 70% -> 约 73%。
- Objective 5：不调整进度；仅记录 `hardware_diagnostics_proof` 后续可被 operator diagnostics 消费。
- Objective 2/3/4：不调整进度。

## KR 拆解和完成情况

- KR1：完成软件侧 proof，startup commands 覆盖 `T=143` echo、`T=142` feedback interval、`T=131` feedback flow。
- KR2：完成软件侧 proof，`T=1` 作为默认 speed mode 示例，`T=13` 继续作为未 HIL 风险示例。
- KR3：完成软件侧 proof，`T=1001` feedback sample 可解析；`/odom` 仍明确为 command integration。
- KR4：完成 focused tests，当前 `test_hardware_diagnostics_proof.py` 10 tests OK。
- KR5：完成 proof config 参数化；实际 Orange Pi UART 设备名仍未确认。

## 本轮核心抓手

- `hardware_diagnostics_proof.py`：离线生成 WAVE ROVER hardware diagnostics proof JSON。
- console script：`hardware_diagnostics_proof`。
- focused tests：覆盖 proof artifact、CLI、非法配置、非数字 config、坏 feedback、T=13/HIL 风险。
- 文档收口：`side2side_check.md`、`final.md` 和 `OKR.md` 明确进度、证据和风险。

## 做什么 / 不做什么

已做：

- 建立 Objective 1 软件侧 proof artifact 和 CLI。
- 修复非数字 config 值直接抛异常的问题，统一返回结构化 `invalid_config`。
- 保留 `risk_flags` 和 `hil_recipe`，明确下一步真实 HIL 命令方向。
- 更新 OKR 进度快照。

未做：

- 未做真实 WAVE ROVER HIL。
- 未跑小修后的完整 smoke。
- 未跑 Docker/Humble build。
- 未接入 operator diagnostics 或手机端页面。
- 未确认 Orange Pi 实际 UART、轮向、速度单位、反馈频率、IMU/电池实测。

## 优先级和验收口径

- P0 离线 proof artifact：通过。
- P0 结构化风险/失败状态：通过。
- P0 focused/hardware package 验证：通过。
- P0 不把 software proof 误写成 HIL：通过。
- P1 operator diagnostics 消费：未纳入本轮，后续推进。

## 对应责任 Engineer

- 本轮实现、测试、修复：`hardware-engineer`。
- 后续真实 WAVE ROVER HIL：`hardware-engineer`。
- 后续 operator diagnostics 消费：`full-stack-software-engineer`。
- 若 HIL 结果影响 launch 或 bringup 集成，由 `robot-software-engineer` 做 ROS2 主链路集成。

## 验证结果

来自 `hardware-engineer` 的本轮证据：

- focused hardware diagnostics proof tests：10 tests OK。
- `py_compile`：OK。
- diff check：OK。
- hardware package tests：24 tests OK。
- 初次完整 smoke：interfaces 6、hardware 23、nav 39、bringup 9、behavior 111、vision 13 tests OK。
- 小修后未重跑完整 smoke，只重跑了 focused + hardware package + py_compile + diff check。

Product/OKR 收口验证：

- doc grep 覆盖 `Objective 1`、`hardware_diagnostics_proof`、`73%`、`HIL`、`side2side`。
- `git diff --check` 覆盖 `OKR.md`、`side2side_check.md`、`final.md`。

## 风险、阻塞和证据链缺口

- 真实 HIL 缺口仍是 Objective 1 最大风险：UART、电气、轮向、速度单位、反馈频率、IMU、电池都没有实车证据。
- 小修后完整 smoke 未重跑，跨包回归风险低但未完全关闭。
- Docker/Humble build 未跑，目标 ROS2 Humble 容器构建证据未补齐。
- `T=13` 仍不得作为默认控制路径，必须等 WAVE ROVER HIL 通过后再评估。
- operator diagnostics 还未消费 `hardware_diagnostics_proof`，Objective 5 不因此抬进度。

## 后续建议

1. 有车环境下由 `hardware-engineer` 跑 no-motion、low-speed `T=1`、`T=13` 专项 HIL recipe。
2. 补一次 Docker/Humble build，确认 console script 在目标构建环境可安装。
3. 另开任务让 `full-stack-software-engineer` 将 proof artifact 接入 operator diagnostics，但不要在 HIL 前向普通用户展示“硬件已通过”。
