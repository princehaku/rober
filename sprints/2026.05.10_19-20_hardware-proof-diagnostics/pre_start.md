# Sprint 2026.05.10 19-20 Hardware Proof Diagnostics - Pre Start

## 状态

- 阶段：pre_start completed。
- 时间：2026-05-10 19:20 Asia/Shanghai。
- Automation ID：`daily-bug-scan`。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。
- 本轮目标：把上一轮 `hardware_diagnostics_proof` 离线 artifact 接入 operator diagnostics 和手机售后诊断显示。

## 用户价值和产品北极星

普通用户不应该看 UART、JSON、轮速映射或厂商源码。手机端和售后同学需要看到的是：当前底盘软件证据是否可读、是否只是 software proof、是否还需要 HIL、配置是否非法、artifact 是否读失败。

本轮继续服务北极星：低成本自主垃圾投递机器人必须让不会电脑和硬件的用户能用手机完成送垃圾任务，并在失败时知道下一步该找人、重跑诊断，还是等待硬件在环验证。硬件 proof 不能被包装成“实车已通过”，只能作为售后诊断证据链的一部分。

## 上轮输入和未完成项

上一轮 `sprints/2026.05.10_18-19_hardware-diagnostics-proof/` 已完成：

- 新增 `hardware_diagnostics_proof.py`，可离线输出 WAVE ROVER proof artifact。
- proof status 已覆盖 `software_proof_ready`、`invalid_config`、`feedback_parse_failed`。
- 小修后 focused tests、hardware 包 tests、py_compile 和 diff check 通过。

上轮留下的本轮输入：

- `hardware_diagnostics_proof` 尚未被 `/api/diagnostics` 消费。
- 手机 operator 页面尚未展示 hardware proof 的售后诊断状态。
- 小修后完整 smoke 未重跑，本轮实现后必须补完整 smoke 护栏。
- 真实 WAVE ROVER HIL、Docker/Humble、真实手机浏览器验证仍不在本轮软件接入范围内。

## OKR 映射

- Objective 5：手机体验与低成本量产边界。本轮直接推进 KR4 远程诊断最小数据包，让手机/售后页面能展示硬件 proof 证据链。
- Objective 1：硬件协议可信底盘。本轮不新增硬件事实和 HIL 证据，只把上一轮 Objective 1 software proof 变成可被 operator diagnostics 消费的证据。
- Objective 2/3/4：不作为本轮主目标；只确保现有 operator gateway、状态页、视觉 diagnostics 不被回归。

## KR 拆解或更新

- Objective 5 KR4：新增 `hardware_proof` diagnostics 字段，包含 proof status、artifact ref、vendor source refs、risk flags、HIL recipe 摘要和 read error。
- Objective 5 KR5：手机页面用普通用户可理解的诊断状态显示 hardware proof，不要求用户读命令行或 ROS2 日志。
- Objective 1 KR4：继续用 behavior/http 单测和 full smoke 作为跨包护栏，但不把本轮视为硬件通过证据。

## 本轮核心抓手

把离线 proof artifact 从“工程师手动跑 CLI 后看 JSON”升级为“operator gateway 自动汇总并在手机/售后诊断面板展示”。关键是状态翻译必须保守：

- `software_proof_ready` -> software proof，可展示为软件证据已生成，同时提示 needs HIL。
- HIL risk flags 存在 -> needs HIL，不能显示硬件已通过。
- `invalid_config` -> invalid config。
- artifact 路径为空、文件不存在、JSON 损坏或 schema 不符合 -> read error。

## 做什么 / 不做什么

做：

- 让 `/api/diagnostics` 返回 hardware proof summary。
- 让手机 operator 页面显示 hardware proof 诊断状态、摘要和下一步动作。
- 更新接口文档和本 sprint 记录。
- 重跑 targeted diagnostics/http tests、py_compile、full smoke 和 diff check。

不做：

- 不打开真实 UART，不连接 WAVE ROVER，不修改硬件参数或 launch 默认值。
- 不把 software proof 显示为 hardware passed。
- 不新增账号系统、云售后平台或 native app。
- 不改视觉 diagnostics 的既有状态语义。
- 不在本计划阶段修改产品代码、测试代码、硬件配置或 `OKR.md`。

## 优先级和验收口径

- P0：`/api/diagnostics` 能在 proof artifact 正常、缺失、非法配置、读失败时稳定返回结构化字段。
- P0：手机页面明确区分 software proof、needs HIL、invalid config、read error。
- P0：现有 operator gateway status、vision diagnostics、collect/dropoff/cancel 行为不回归。
- P0：完整 smoke 重跑，关闭上一轮小修后的跨包验证缺口。
- P1：接口文档说明字段 contract 和产品边界。

## 对应责任 Engineer

- 实现、测试、修复、`tech-done.md`：`full-stack-software-engineer`。
- 如 proof 字段解释需要硬件事实补充，可只读咨询 `hardware-engineer`；本轮不让 hardware owner 改代码。
- Product/OKR Owner 在实现后负责验收口径检查、`side2side_check.md`、`final.md` 和必要的 OKR 收口。

## 风险、阻塞和证据链缺口

- 最大产品风险：页面把 software proof 误导成硬件实测通过。所有文案和字段都必须保守。
- 最大工程风险：diagnostics 读取 artifact 时抛异常导致 `/api/diagnostics` 不可用；必须降级为 structured read error。
- 上车缺口：真实 UART、轮向、速度单位、反馈频率、IMU、电池、T=13 仍没有 HIL 证据。
- 验证缺口：本轮计划阶段只做文档 diff check；实现阶段必须由 owner 运行完整验收命令。

## 需要创建或更新的 sprint 文档

本计划阶段创建：

- `sprints/2026.05.10_19-20_hardware-proof-diagnostics/pre_start.md`
- `sprints/2026.05.10_19-20_hardware-proof-diagnostics/prd.md`
- `sprints/2026.05.10_19-20_hardware-proof-diagnostics/tech-plan.md`

实现和收口阶段必须继续更新：

- `sprints/2026.05.10_19-20_hardware-proof-diagnostics/tech-done.md`
- `sprints/2026.05.10_19-20_hardware-proof-diagnostics/side2side_check.md`
- `sprints/2026.05.10_19-20_hardware-proof-diagnostics/final.md`
