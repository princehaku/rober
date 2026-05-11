# Sprint 2026.05.11 02-03 Elevator Assisted Delivery Dry Run - PRD

## 状态

- 阶段：prd completed。
- 时间：2026-05-11 02:03 Asia/Shanghai。
- Owner：`product-okr-owner`。
- 产品切片：电梯 assisted delivery 可选 dry-run 功能骨架。

## 背景

`docs/product/elevator_assisted_delivery.md` 已定义 H2/受控场景的用户流程、状态机边界、手机文案、语音提示和验收层级。当前缺口是它还停留在产品 contract，没有进入行为 dry-run、任务记录和 operator/diagnostics 状态契约。

本轮优先 Objective 2，因为当前 OKR 快照中 Objective 2 约 74%，是最低完成度方向。目标是让“送垃圾任务闭环”继续往功能前进，而不是继续只补大面积测试。

## 用户价值和北极星

目标用户仍是不懂 ROS2、串口、地图和硬件调试的普通手机用户。电梯 assisted delivery 的最小价值是：当送垃圾任务需要跨楼层时，用户能在手机上看到小车当前是在等电梯、请求帮忙按楼层、等待目标楼层、需要人工协助，任务失败也能知道原因。

本轮不追求真实跨楼层成功，而是让工程系统先能证明：

- 状态链路可演练。
- 手机状态可解释。
- 语音提示 contract 可复用。
- 任务记录可复盘。
- 默认关闭，不影响当前 MVP 送垃圾主链路。

## OKR 映射

- Objective 2 / KR6：定义并验证 elevator assisted delivery 状态链路。本轮推进到软件 dry-run 骨架和任务记录证据。
- Objective 5 / KR6：定义跨楼层 trash delivery 的手机/语音体验。本轮推进到 operator/status/diagnostics contract。
- Objective 4 / KR6：补齐电梯场景感知 contract。本轮只接 dry-run 证据 schema，不声明真实识别。

## KR 拆解或更新

本轮不直接修改 `OKR.md` 进度数字；工程完成后才可按证据判断是否小幅更新软件完成度。

- KR2.6-A：行为层支持默认关闭的 `elevator_assist` dry-run 子流程。
- KR2.6-B：`TrashCollection` 或送达任务记录能写入 elevator 状态转移、模拟事件、失败原因和人工接管原因。
- KR5.6-A：operator/status 能输出电梯状态对应的 `phone_copy` 和 `speaker_prompt`。
- KR5.6-B：diagnostics 能提供机器可读的 elevator dry-run 状态和最近一次任务记录引用。
- KR4.6-A：定义 `door_open`、`door_closed_or_unknown`、`target_floor_confirmed`、`unsafe_to_exit` 等 dry-run 证据字段，后续可替换成真实感知。

## 本轮核心抓手

从产品 contract 推进到工程可执行 dry-run：

1. 行为状态：用模拟事件走完电梯子状态，不依赖真实电梯。
2. 任务记录：把状态转移和失败原因写进 task record，而不是只在日志里出现。
3. 用户触点：operator 手机文案和 speaker prompt 复用 `docs/product/elevator_assisted_delivery.md` 的提示词。
4. 默认关闭：未启用时现有 MVP 不变。
5. 测试围栏：只写覆盖新增行为和网关契约的 targeted tests。

## 做什么

- 增加可选参数或配置：`elevator_assist_enabled=false`、`elevator_assist_mode=dry_run`。
- 增加 dry-run 输入契约：模拟门开、已进入轿厢、目标楼层确认、目标楼层开门、驶出完成、超时/证据冲突。
- 增加状态输出契约：`elevator_assist.state`、`elevator_assist.phase`、`elevator_assist.requires_human_help`、`elevator_assist.reason`、`elevator_assist.evidence`。
- 增加任务记录字段：`elevator_events` 或等价结构，记录时间、状态、事件、结果和用户可见提示。
- 增加 operator/diagnostics 显示：手机文案覆盖到达电梯厅、等待开门、请求按楼层、等待目标楼层、目标楼层证据不可靠、成功驶出。

## 不做什么

- 不启用真实电梯流程。
- 不做楼层识别、门识别或驶出视觉模型。
- 不做 TTS/喇叭实机播放，只保留 speaker prompt contract。
- 不新增硬件假设，不修改 ESP32/WAVE ROVER 固件和硬件桥。
- 不扩大测试到无关模块；不为了指标堆测试文件。
- 不在没有实机证据时宣称 Objective 2 完成。

## 优先级

- P0：默认关闭、dry-run 状态链路、task record、operator/status/diagnostics contract、targeted tests。
- P1：launch 参数透传和最小 smoke 验证。
- P2：未来真实感知接入、受控电梯样本采集、TTS/喇叭播放验证、实景三连验收。

## 验收口径

产品验收只看证据，不看愿景：

- 默认关闭：相关测试证明未启用 `elevator_assist` 时现有送达结果和 operator 状态不受影响。
- 完整 dry-run：模拟 happy path 能记录从等待电梯到驶出并恢复送达的状态序列。
- 失败路径：至少覆盖门未开超时、目标楼层证据不可靠、驶出不安全或超时。
- 手机可解释：每个电梯关键状态有普通用户可读 `phone_copy`，不是只有内部错误码。
- 语音 contract：进入电梯后输出指定求助提示 `你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,`，但不声明实机播放完成。
- 任务可复盘：task record / diagnostics 能关联 elevator 事件、原因、结果和记录路径。
- 测试围栏：targeted tests + `py_compile` + scoped diff check 通过；必要时由工程 agent 跑 smoke。

## 对应责任 Engineer

- `robot-software-engineer`：主责，负责行为 dry-run、task record、bringup 参数、集成验证和 `tech-done.md`。
- `full-stack-software-engineer`：协作，负责 operator gateway/status/diagnostics 的状态契约和手机文案。
- `autonomy-engineer`：协作，负责 dry-run evidence schema 和未来真实感知替换边界。
- `hardware-engineer`：本轮不派实现；没有硬件改动。若后续触及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压、固件或机械尺寸，必须先查 `docs/vendor/VENDOR_INDEX.md`。

## 风险和证据链

- dry-run 是软件证据，不是实机跨楼层能力。
- 真实电梯场景仍需要观察员、急停、人工接管和受控路线。
- 目标楼层识别仍是最大产品风险，不能用固定等待时间冒充证据。
- 工程完成后必须补 `tech-done.md`，并注明测试结果、未完成实机验证和是否影响 OKR 进度。
