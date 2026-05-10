# Sprint 2026.05.10 18-19 Hardware Diagnostics Proof - Pre Start

## 状态

- 阶段：pre-start completed。
- 时间：2026-05-10 18:09 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`hardware-engineer`。
- 任务类型：Objective 1 功能推进；测试只作为护栏。

## 上轮未完成项

- 上一轮 `sprints/2026.05.10_17-18_visual-gate-proof/` 已完成 Objective 3/4 的 fixed-route visual gate 离线 proof artifact，并提交 `6fa4894 Add fixed route visual gate proof`。
- OKR 当前快照约为：Objective 1 70%、Objective 2 74%、Objective 3 73%、Objective 4 70%、Objective 5 74%。
- Objective 1 的主要缺口不是再补口头说明，而是把 WAVE ROVER JSON 协议、启动配置、反馈解析、参数边界和本地验证证据沉淀成无实机也能运行的 diagnostics/proof artifact，为后续 operator diagnostics 和 HIL 预留接口。
- 本轮不选择真实 WAVE ROVER HIL，因为当前要求是无实机也能推进功能；如实现涉及协议字段、命令 ID、UART、波特率、速度单位或反馈字段，`hardware-engineer` 必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向的本地 vendor 文件。

## 本轮目标

推进 Objective 1“硬件协议可信底盘”：

- 新增一个离线可验证的 hardware diagnostics/proof artifact 或 CLI。
- 证明当前硬件桥的协议编码、启动配置、反馈解析、配置边界和 smoke 命令计划能被结构化导出。
- 不接真实串口、不要求 WAVE ROVER 实机、不改 launch 硬件默认值。
- 为后续 operator diagnostics/HIL 留出稳定字段：vendor sources、command mode、startup commands、feedback sample parse、cmd_vel examples、risk flags、next HIL command recipe。

## 用户价值和产品北极星

- 用户价值：普通用户最终不需要懂串口、ROS2 或厂商协议；售后和工程同学必须能在没有实车时先判断“软件侧底盘协议证据是否完整”，减少上车时才发现协议、参数或反馈字段不可信的成本。
- 产品北极星：低成本垃圾投递机器人必须先有可信底盘控制层；手机一键发车之前，底盘协议、停止路径、反馈和配置边界都要能被解释和复盘。

## OKR 映射

- 主推进 Objective 1：打通官方硬件协议，建立可信底盘控制层。
  - 对齐 KR1：证明 UTF-8 JSON + newline、echo、反馈间隔和反馈流启动配置。
  - 对齐 KR2：证明默认 `speed` 模式走 `T=1` 左右轮命令，`ros` 模式 `T=13` 仍标注为需硬件验证。
  - 对齐 KR3：证明 `T=1001` feedback sample 能被解析为左右速度、IMU 姿态和电压；继续标注 `/odom` 为命令积分，不当作实测里程计。
  - 对齐 KR4：用 focused tests 锁定 proof 输出和坏数据/配置边界。
  - 对齐 KR5：把 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps` 等参数进入 proof 或 CLI 入参，不硬编码 Orange Pi 实际设备名。
- 不推进 Objective 2/3/4/5 的进度。本轮不改行为状态机、导航、视觉或手机 UI。

## 本轮核心抓手

由 `hardware-engineer` 在 `ros2_trashbot_hardware` 内新增一个 dependency-light diagnostics/proof helper/CLI，直接复用或调用现有 `esp32_bridge.py` 中的纯函数，输出结构化 JSON。它应该能被单测直接调用，也能作为 console script 运行。

## 做什么 / 不做什么

做：

- 新增硬件协议 diagnostics/proof helper/CLI。
- 输出当前协议状态、vendor source 引用、启动命令、cmd_vel 样例、反馈样例解析、配置校验结果、HIL 待验证项和风险标记。
- 新增 focused 单测，覆盖 proof JSON、配置边界、T=13 未 HIL 风险、坏反馈样例。
- 更新本 sprint `tech-done.md`，记录实际改动、验证结果、接口影响和剩余风险。

不做：

- 不接真实 WAVE ROVER，不打开真实 UART。
- 不修改 vendor 文件、factory firmware、AGENTS、OKR。
- 不改硬件 launch 默认参数或 Orange Pi 串口设备默认值。
- 不把离线 proof 宣称为 HIL 通过。
- 不新增手机 UI 或 operator diagnostics 接入；本轮只给后续消费预留稳定 artifact。

## 优先级和验收口径

P0：

- CLI/纯函数能在无 ROS2 daemon、无真实串口、无 WAVE ROVER 环境下生成 diagnostics proof JSON。
- proof JSON 至少包含 `vendor_sources`、`config`、`startup_commands`、`cmd_vel_examples`、`feedback_sample`、`risk_flags`、`hil_recipe`。
- 明确标注 `T=13` ROS mode 需要 HIL；默认 `speed` 模式基于 `T=1`。
- 单测覆盖正常 proof、配置非法、反馈坏数据、风险标记。

P1：

- console script 名称和输出参数清晰，后续能被 operator gateway 或 HIL runbook 消费。
- `tech-done.md` 写清 vendor 来源、验证命令、失败定位和剩余风险。

## Owner

- 主责：`hardware-engineer`。
- 协作：本轮不需要 Robot Platform、Autonomy 或 Full-Stack 改代码。
- Product Owner：只负责本轮价值、范围、验收口径和 sprint planning；不写产品代码或测试代码。

## 风险、阻塞和证据链缺口

- 离线 proof 只证明软件侧协议证据链，不证明真实串口、电气连接、轮向、速度单位、反馈频率或 IMU/电池实测正确。
- `T=13` 虽有 vendor firmware 注释，但本项目仍要求硬件验证后才能作为默认 `/cmd_vel` 映射。
- Orange Pi 实际 UART 设备名仍必须上车确认，不能从 Raspberry Pi vendor 样例推断。
- 后续仍需真实 WAVE ROVER HIL、Docker/Humble build、operator diagnostics 消费和上车验收记录。

## 需要创建或更新的 sprint 文档

- 已创建：`sprints/2026.05.10_18-19_hardware-diagnostics-proof/pre_start.md`
- 已创建：`sprints/2026.05.10_18-19_hardware-diagnostics-proof/prd.md`
- 已创建：`sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-plan.md`
- implementation 完成后必须由 `hardware-engineer` 更新：`sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-done.md`
- 验收或复盘阶段再更新：`side2side_check.md`、`final.md`
