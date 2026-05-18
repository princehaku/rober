# Sprint 2026.05.19_01-02 Mobile Elevator Action Feedback Display - PRD

## 用户价值和产品北极星

普通用户的核心问题不是“Robot 是否写了 action feedback”，而是手机上能否在任务进行时解释小车为什么停在电梯相关阶段、下一步需要等待什么、是否需要人工协助。本轮产品价值是把 `TrashCollection.Feedback.current_step=elevator:<phase>` 变成手机可读的实时阶段展示，减少用户误判、等待焦虑和售后沟通成本。

北极星仍是低成本 ROS2 自主垃圾投递机器人：用户只用手机完成送垃圾任务，手机端能解释状态和异常。本轮只推进 Objective 4 / Objective 2 的可解释性，不证明真实手机、真实电梯、真实送达或 delivery success。

## OKR 映射

- Objective 4：对应 KR6 / KR7。手机端需要用中文优先文案展示跨楼层 trash delivery 的当前阶段和人工协助原因，不暴露 raw JSON、ROS topic、串口或底层控制参数。
- Objective 2：对应 KR6 / KR7。电梯 assisted delivery 已进入主链 action feedback；本轮要求手机只读消费这个主链反馈，帮助用户理解等待开门、进入电梯、请求按楼层、等待目标楼层、驶出和恢复送达。
- Objective 5：本轮不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。
- Objective 1：本轮不推进。没有真实 WAVE ROVER/UART/HIL 或 PR #5 2D LiDAR / ToF 真实材料。

## KR 拆解

1. Full-Stack 将 `current_step=elevator:<phase>` 映射为手机只读实时阶段展示。
2. Full-Stack 支持至少这些阶段：`waiting_elevator_open`、`entering_elevator`、`requesting_floor_help`、`waiting_target_floor`、`exiting_elevator`、`resume_delivery`。
3. Full-Stack 在字段缺失、非 `elevator:` 前缀、未知 phase、offline、blocked、pending ACK 或 manual takeover 时 fail closed，不推断成功。
4. Full-Stack 保持 Start Delivery、Confirm Dropoff、Cancel gating 完全不变。
5. Robot 只读核对 action feedback 字段来源、阶段值、message 和证据边界；不得扩大为新 robot 状态或真实现场证据。
6. Product closeout 在完成后确认仍为 `software_proof` / `not_proven`，并保留 `delivery_success=false`、`primary_actions_enabled=false`。

## 本轮核心抓手

用户在手机上看到的是“电梯辅助实时阶段”，不是历史材料 checklist、不是 raw diagnostics、不是成功证明。展示必须从现有 status/diagnostics 或 action feedback 输入读取 `current_step=elevator:<phase>`，然后转成短中文阶段标题、说明和下一步提示。

## 功能范围

必须做：

- 在 `mobile/web` 中增加只读实时电梯阶段展示，优先消费 `current_step=elevator:<phase>`。
- 阶段展示必须中文优先，避免暴露 ROS action/raw topic 名称；面向用户可用标题示例：等待电梯开门、进入电梯、请求帮忙按楼层、等待目标楼层、驶出电梯、继续送往垃圾站。
- 若存在 action `message` 且 phone-safe，可显示为补充说明；不得展示 artifact path、serial/UART、baudrate、WAVE ROVER 参数、credentials、DB/queue URL、raw JSON、完整 artifact 或 checksum。
- 保持现有 Start Delivery、Confirm Dropoff、Cancel gating，不因展示电梯阶段而启用任何主操作。
- 更新相关 `docs/product/mobile_user_flow.md` 或接口文档，说明该展示仍是 `software_proof` / `not_proven`。

不做：

- 不接入真实手机设备、production app、真实 PWA prompt/user choice。
- 不实现真实电梯识别、真实 TTS、真实 Nav2/fixed-route、真实 route completion、真实 dropoff/cancel completion。
- 不处理 PR #5 的 2D LiDAR / ToF 采购、安装、接线、电源、标定或 HIL-entry。
- 不做 Objective 5 云、公网 HTTPS/TLS、4G/SIM、OSS/CDN、DB/queue 或 worker/cutover。

## 优先级

P0：

- 识别 `current_step=elevator:<phase>` 并渲染只读实时阶段。
- 缺失或未知时 fail closed。
- 保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。
- 测试覆盖阶段映射、未知阶段、缺失字段和主操作不放行。

P1：

- 与已有“电梯辅助状态”或 diagnostics panel 做文案去重，避免首屏堆叠重复状态。
- 兼容 `/api/status`、`phone_readiness`、`/api/diagnostics` 或 nested diagnostics summary 中的 action feedback 形态。

P2：

- 后续真实手机/浏览器验收、production app、PWA prompt/user choice 和外部云材料，不在本轮实现。

## 验收口径

- 手机页面能在 fixture 或 targeted smoke 中展示 `current_step=elevator:<phase>` 对应的电梯实时阶段。
- unknown/missing/non-elevator current_step 不显示成功，不放行主操作，用户能看到保守 fallback。
- Start Delivery、Confirm Dropoff、Cancel gating 与改动前保持一致；`primary_actions_enabled=false` 时三者不得被启用。
- 输出和文档明确 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不出现真实手机通过、真实电梯通过、真实 Nav2/fixed-route、HIL、真实投放、真实 cancel/dropoff completion 或 delivery success 的表述。

## 对应责任 Engineer

- `full-stack-software-engineer`：主责实现、fixture、mobile web tests、docs/product 更新。
- `robot-software-engineer`：只读核对 action feedback contract 和兼容输入；必要时补接口文档，不改主链状态机。
- `product-okr-owner`：收口 OKR、验收边界和 sprint 文档，确认 PR #4 / PR #5 证据没有被误写成真实材料。

## 风险、阻塞和证据链

- 真实手机、真实电梯、真实路线、真实 WAVE ROVER/UART/HIL、真实 O5 external proof 均缺失。
- `current_step=elevator:<phase>` 是 action feedback 的实时展示信号，不是 delivery result。
- 若后续执行发现 operator gateway 当前不暴露 action feedback，必须先由 Robot 给出最小兼容 summary 或文档化现状；Full-Stack 不得用旧 checklist 伪造实时阶段。
