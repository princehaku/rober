# Sprint 2026.05.10 18-19 Hardware Diagnostics Proof - Side2Side Check

## 状态

- 阶段：Product/OKR acceptance completed。
- 时间：2026-05-10 18:49 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`hardware-engineer`。
- 验收结论：通过软件侧验收；不等同于 WAVE ROVER HIL 或上车通过。

## 用户价值和产品北极星

- 用户价值：工程/售后同学现在可以在无实车、无 ROS2 daemon、无真实 UART 的环境下生成硬件协议 proof artifact，快速判断底盘协议软件证据是否完整、配置是否非法、下一步 HIL 要跑什么。
- 产品北极星：低成本垃圾投递机器人要先拥有可信底盘控制层；本轮把 WAVE ROVER JSON 协议、启动配置、反馈解析、风险和 HIL recipe 从分散代码推进为可复盘 artifact。

## OKR 映射和 KR 验收

- Objective 1：进度从约 70% 调整到约 73%。
- KR1：通过 proof artifact 展示 UTF-8 JSON newline、UART echo、feedback interval、feedback flow startup commands。
- KR2：默认 `speed` 模式继续基于 `T=1` 左右轮命令；`T=13` ROS mode 只作为未 HIL 示例和风险标记。
- KR3：`T=1001` feedback sample 可离线解析为左右速度、姿态和电压；`/odom` 仍标记为 command integration。
- KR4：focused tests 覆盖正常 proof、CLI 输出、非法配置、非数字 config、坏 feedback、T=13/HIL 风险和 startup command IDs。
- KR5：proof config 暴露 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`、`feedback_interval_ms` 等参数，不把 Orange Pi 实际 UART 写死为已确认事实。
- Objective 5：本轮只说明后续 operator diagnostics 可消费该 artifact，不直接抬进度。
- Objective 2/3/4：本轮不抬进度。

## 本轮核心抓手

- 新增 `hardware_diagnostics_proof.py` 和 console script，把硬件协议 proof 输出为结构化 JSON。
- 将 `invalid_config` 作为结构化状态，覆盖非数字 config 值，避免配置错误在 proof 生成阶段直接抛异常。
- 在 artifact 中保留 `risk_flags` 和 `hil_recipe`，把“软件侧已证明”和“实车仍待验证”分开。

## 做什么 / 不做什么

做：

- 验收 `hardware_diagnostics_proof` 是否满足 PRD/tech-plan 的离线 proof artifact 要求。
- 将小修后的 focused/hardware package 结果和小修前完整 smoke 证据写入 sprint 收口。
- 更新 `OKR.md` Objective 1 进度和缺口。

不做：

- 不声明真实 UART、WAVE ROVER HIL、轮向、速度单位、反馈频率、IMU 或电池已通过。
- 不改产品代码、测试代码、vendor 文件、launch 参数或硬件配置。
- 不把 operator diagnostics 手机端消费计入 Objective 5 进度。

## 优先级和验收口径

- P0：离线 proof helper/CLI 可生成包含 `vendor_sources`、`config`、`startup_commands`、`cmd_vel_examples`、`feedback_sample`、`risk_flags`、`hil_recipe` 的 artifact。结论：通过。
- P0：`invalid_config`、`feedback_parse_failed`、`hil_required`、`ros_mode_t13_unverified` 等状态/风险可结构化表达。结论：通过。
- P0：验证证据不能把离线 proof 说成 HIL。结论：通过，文档已明确剩余 HIL 缺口。
- P1：后续 operator diagnostics 或 HIL runbook 可消费 artifact。结论：字段已具备，尚未接入。

## 对应责任 Engineer

- 已完成实现和验证：`hardware-engineer`。
- 后续 HIL/硬件证据主责：`hardware-engineer`。
- 后续 operator diagnostics 消费主责：`full-stack-software-engineer`，需另开 sprint 或任务。

## 验证证据

- focused hardware diagnostics proof tests：10 tests OK。
- `py_compile`：OK。
- diff check：OK。
- hardware package tests：24 tests OK。
- 初次完整 smoke：interfaces 6、hardware 23、nav 39、bringup 9、behavior 111、vision 13 tests OK。
- 小修后未重跑完整 smoke；小修只重跑 focused + hardware package + py_compile + diff check。

## 风险、阻塞和证据链缺口

- 真实 WAVE ROVER HIL 未做，本轮不能关闭 Objective 1。
- 小修后未重跑完整 smoke，跨包回归证据停留在小修前。
- Docker/Humble build 本轮未跑。
- Orange Pi 实际 UART 设备名、真实接线、轮向、速度单位、反馈频率、IMU 姿态、电池电压仍需上车验证。
- `T=13` ROS mode 仍必须维持未验证状态，不能成为默认 `/cmd_vel` 映射。

## 需要创建或更新的 sprint 文档

- 已更新：`OKR.md`。
- 已创建：`sprints/2026.05.10_18-19_hardware-diagnostics-proof/side2side_check.md`。
- 下一步创建：`sprints/2026.05.10_18-19_hardware-diagnostics-proof/final.md`。
