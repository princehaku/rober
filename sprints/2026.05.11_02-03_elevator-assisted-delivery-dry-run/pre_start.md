# Sprint 2026.05.11 02-03 Elevator Assisted Delivery Dry Run - Pre Start

## 状态

- 阶段：pre-start completed。
- 时间：2026-05-11 02:03 Asia/Shanghai。
- Sprint 目录：`sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run/`。
- 本轮 owner：`product-okr-owner`。
- 执行意图：开始下一轮迭代，用 team 继续推进 OKR，优先补当前完成度最低的 Objective 2。

## 用户原始要求

用户要求：“开始下一轮迭代，用team继续完成OKR，重新在功能往前走，别测试代码一堆，测试只围栏。优先推进OKR完成度低的部分，记得最后要提交git”。

## 上轮输入和未完成项

- 上轮 `2026.05.11_01-02_elevator-assisted-delivery-okr` 已把 elevator assisted delivery 纳入 `OKR.md` 和 `docs/product/elevator_assisted_delivery.md`。
- 上轮明确电梯能力是 H2/受控场景，不是当前 MVP 已完成能力，不默认新增硬件，不让 ESP32/WAVE ROVER 下位机承担电梯识别或语音决策。
- 当前 OKR 快照中 Objective 2 约 74%，低于 Objective 1、3、4、5；本轮优先推进“可恢复送垃圾任务闭环”。
- Objective 2 的关键缺口仍是行为层真实运行证据；本轮先做默认关闭的软件 dry-run 骨架，不声明实机可用。

## 用户价值和产品北极星

北极星仍是低成本 ROS2 自主垃圾投递机器人：普通用户只用手机把垃圾交给小车，小车完成受控路线送达、异常解释和人工接管。

本轮用户价值不是“全自动乘电梯”，而是把跨楼层送垃圾流程拆成软件可演练、手机可理解、任务可复盘的状态链路。这样后续工程同学可以在没有实机电梯和不新增硬件的前提下，先验证行为状态、任务记录、operator 状态和 diagnostics 契约是否成立。

## OKR 映射

- Objective 2：主目标。推进 KR6 的 elevator assisted delivery 状态链路，从产品 contract 进入行为 dry-run、任务记录和失败路径。
- Objective 5：副目标。让 operator 手机状态和 diagnostics 能解释电梯等待、求助、目标楼层不可靠和人工接管。
- Objective 4：副目标。只定义感知证据字段和模拟输入，不做真实视觉算法或相机上车。

## 本轮核心抓手

做一个默认关闭的 `elevator_assist` dry-run 骨架计划：

- 行为层能用模拟事件驱动电梯子状态。
- 任务记录能留下电梯状态转移、模拟证据、失败原因和人工接管原因。
- operator/status/diagnostics 能输出手机文案、speaker prompt 和机器可读的 elevator 状态。
- bringup/launch 只暴露默认关闭的参数，不改变现有 MVP 主链路。
- 测试只做围栏：针对性行为/网关测试、`py_compile`、scoped diff check；必要时最终 smoke 由工程 agent 跑。

## 做什么 / 不做什么

做：

- 做电梯 assisted delivery 可选 dry-run 功能骨架。
- 做状态契约、任务记录契约、operator/diagnostics 契约和最小 launch 参数边界。
- 做 targeted tests，保证默认关闭、不影响现有送达流程。

不做：

- 不做实机电梯验证。
- 不做真实视觉门开/楼层识别算法。
- 不新增机械臂、深度相机、电梯控制器、ESP32 固件、电气接线或 WAVE ROVER 协议改动。
- 不把测试扩成大面积测试代码堆叠；测试只作为功能围栏。
- 不提升 OKR 实机完成度，除非后续工程实现和验证给出证据。

## 优先级和验收口径

P0：

- 默认关闭：未显式启用时现有 `TrashCollection`、fixed-route、operator gateway 状态不变。
- dry-run 可走完整链路：`approaching_elevator -> waiting_elevator_open -> entering_elevator -> requesting_floor_help -> waiting_target_floor -> exiting_elevator -> resume_delivery`。
- 失败可解释：门未开、目标楼层证据不可靠、驶出超时都能进入 `needs_human_help` 或明确失败结果。
- task record 包含 elevator 状态转移、模拟事件、手机文案、speaker prompt、失败原因。
- diagnostics/status 能暴露机器可读 `elevator_assist` 字段和普通用户可读文案。

P1：

- dry-run 输入可以从参数或状态文件驱动，便于后续实景证据替换。
- launch 参数在 `autonomous.launch.py` / `bringup.launch.py` 中有默认关闭边界。
- 工程完成后由 Robot Platform 主责做集成验收。

## 对应责任 Engineer

- 主责：`robot-software-engineer`。负责行为状态机、任务记录、launch 参数集成和最终集成验证。
- 协作：`full-stack-software-engineer`。负责 operator gateway/status/diagnostics 手机文案和 speaker prompt contract。
- 协作：`autonomy-engineer`。负责电梯门、目标楼层、驶出条件的 dry-run 证据 schema；本轮不做真实识别。
- 暂不介入：`hardware-engineer`。本轮不涉及 UART、引脚、电压、波特率、固件、机械安装或 WAVE ROVER 实机参数；后续进入硬件事项时必须先查 `docs/vendor/VENDOR_INDEX.md`。

## 风险、阻塞和证据链缺口

- 风险：默认关闭边界做不好会污染现有送垃圾主链路。
- 风险：手机文案如果只给错误码，会违背普通用户只用手机的产品目标。
- 风险：模拟 dry-run 不能等同实机电梯成功；最终文档和工程输出必须保持这个口径。
- 阻塞：真实门开/目标楼层/驶出证据还没有相机样本和受控电梯数据。
- 证据链缺口：本轮 sprint 还未进入工程实现；完成后必须补 `tech-done.md`，并记录 targeted tests、py_compile、scoped diff check 和剩余实机风险。

## 需要创建或更新的 sprint 文档

- 本轮创建并完成：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程实现后必须更新：`tech-done.md`。
- 验收或阶段收口后再更新：`side2side_check.md`、`final.md`。
