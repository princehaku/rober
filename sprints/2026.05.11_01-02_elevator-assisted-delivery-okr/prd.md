# Sprint 2026.05.11 01-02 Elevator Assisted Delivery OKR - PRD

## 状态

- 阶段：prd completed。
- 时间：2026-05-11 01:02 Asia/Shanghai。
- Product Owner：`product-okr-owner`。

## 用户价值和产品北极星

用户价值：普通手机用户在跨楼层楼宇场景里，不需要懂 ROS2、硬件或电梯系统，只需要把垃圾交给小车并选择目标楼层/垃圾站。小车把“进出电梯”拆成可解释、可求助、可接管的 assisted delivery 流程。

北极星：低成本 trash delivery。电梯能力是 H2/受控场景增强，不改变“用户交付垃圾 -> 小车送到垃圾站/垃圾桶点位 -> 投放/提醒 -> 返回/待命”的核心闭环。

## OKR 映射

- Objective 2：可恢复送垃圾任务闭环
  - 新增 KR6：电梯子状态链路，包括等待开门、进入电梯、语音求助、等待目标楼层、目标楼层开门驶出。
- Objective 4：感知模块产品化
  - 新增 KR6：电梯门开/关、目标楼层到达、可驶出证据进入感知 contract。
- Objective 5：手机体验与量产边界
  - 新增 KR6：跨楼层 trash delivery 的手机/语音体验和人工协助边界。

## KR 拆解或更新

- KR-A：OKR 写清电梯 assisted delivery 是 H2/受控场景，不是当前 MVP 完成能力。
- KR-B：产品文档写清最小用户流程和指定语音提示：“你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,”。
- KR-C：状态机边界覆盖电梯厅等待、进入、求助、等待目标楼层、驶出、恢复送达。
- KR-D：识别要求覆盖开门、目标楼层、驶出安全和失败证据。
- KR-E：人工协助边界明确：小车不按按钮、不控制电梯、不默认新增机械臂或昂贵硬件。

## 本轮核心抓手

1. 把 CEO 的电梯场景翻译成 OKR/KR，而不是把愿景写成已完成事实。
2. 用产品 contract 约束后续工程实现：行为、感知、语音、手机状态各自有 owner。
3. 保持低成本、手机优先和 trash delivery 主线，不扩张到电梯改造或机械臂方案。

## 做什么 / 不做什么

做：

- 更新 `OKR.md` 的北极星、战略定位、Objective/KR、H2 路线、风险、下一步建议和当前进度快照。
- 新增 `docs/product/elevator_assisted_delivery.md`。
- 新建独立 sprint 留档并完成文档验证。

不做：

- 不改 `src/`。
- 不改 `docs/vendor/`、`docs/hardware/` 或 `README.md`。
- 不改硬件 proof 参数门禁 sprint。
- 不新增硬件引脚、串口、波特率、电压或机械假设。
- 不宣称电梯能力已经实机完成。

## 优先级和验收口径

- P0：OKR 明确 H2/受控场景定位和 Objective/KR 映射。
- P0：产品文档覆盖流程、语音、状态机、识别、人工协助和验收口径。
- P0：文档明确能力归属在 Orange Pi/ROS2 上位机行为/感知/语音编排，不是 ESP32 下位机能力。
- P0：最小文档验证命令通过。
- P1：后续实现 owner 和风险证据链写清。

## 对应责任 Engineer

- 本轮产品 owner：`product-okr-owner`。
- 后续实现：
  - `robot-software-engineer` 负责行为状态机和任务记录。
  - `autonomy-engineer` 负责门开/目标楼层/驶出证据。
  - `full-stack-software-engineer` 负责手机状态、diagnostics、语音提示 contract。
  - `hardware-engineer` 仅在涉及硬件事实和安装时介入。

## 风险、阻塞和需要补齐的证据链

- 风险：电梯场景被误读成全自动乘梯或已完成能力。
- 风险：目标楼层识别不可靠会导致错层驶出。
- 风险：电梯门识别误判会影响安全。
- 阻塞：后续需要受控楼宇路线、观察员、安全停止策略和真实感知证据。
- 证据链：本轮只有产品/文档证据；后续至少需要软件 dry-run、手机/语音 contract 测试和受控实景验证。

## 需要创建或更新的 sprint 文档

- `pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、`side2side_check.md`、`final.md`。
