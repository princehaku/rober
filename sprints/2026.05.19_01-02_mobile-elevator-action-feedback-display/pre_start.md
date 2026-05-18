# Sprint 2026.05.19_01-02 Mobile Elevator Action Feedback Display - Pre Start

## sprint_type

sprint_type: epic

## 本轮启动结论

本轮启动 Objective 4 / Objective 2 的跨 owner Epic sprint：让 `mobile/web` 在既有状态或 diagnostics 输入里识别并展示 `TrashCollection.Feedback.current_step=elevator:<phase>`，把上轮 Robot action feedback 变成普通手机用户可读的实时电梯阶段展示。

本轮由 `full-stack-software-engineer` 主责实现，`robot-software-engineer` 做只读或轻量接口事实协同，`product-okr-owner` 做阶段验收和 OKR closeout。

## 用户价值和产品北极星

用户价值：用户发车后不需要理解 ROS action、task record 或 raw diagnostics，也能在手机上看到小车正处在等待电梯开门、进入电梯、请求按楼层、等待目标楼层、驶出电梯、恢复送达中的哪一步。

产品北极星：普通手机用户完成低成本 trash delivery，手机端能解释当前状态和下一步动作；本轮推进的是实时可解释性，不是证明真实电梯、真实手机、真实送达或 delivery success。

## 背景证据

- `OKR.md` 4.1 当前快照显示 Objective 5 约 68%，数字最低，但 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。本轮不继续 Objective 5 local metadata。
- `OKR.md` 4.1 当前快照显示 Objective 1 约 81%，但没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，也没有 PR #5 相关 2D LiDAR / ToF 真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。本轮不继续本地硬件 wrapper。
- PR #4 要求 elevator-assisted delivery 进入主链；上轮 sprint `2026.05.19_00-01_elevator-assist-action-feedback-mainline/final.md` 已完成 Robot action feedback 主链路软件证据。
- PR #5 Codex Review 暴露 `production_hardware_boundary.md` 默认硬件集与 mandatory 2D LiDAR / ToF baseline 矛盾、OKR lowest narrative 漂移、mandatory sensor assumptions 缺 vendor source。本轮不把手机展示写成 PR #5 真实硬件材料补齐。
- 上轮 final 明确后续：Full-Stack 应消费 `TrashCollection.Feedback.current_step=elevator:<phase>` 做只读实时手机展示；不得改变 Start Delivery、Confirm Dropoff、Cancel gating，也不得声明真实手机或 delivery success。

## 上轮未完成项

- Full-Stack 尚未把 action feedback 的 `current_step=elevator:<phase>` 映射为手机端实时阶段展示。
- Robot 侧已发布 phone-safe feedback，但本轮仍需确认可消费字段、兼容 status/diagnostics 输入位置和 fail-closed 文案边界。
- Product 侧需要在实现后核对 Objective 4 / Objective 2 证据边界，确保 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 没有被 UI 文案放大。

## 本轮核心抓手

把 `current_step=elevator:<phase>` 从“Robot action feedback 字段”推进为“手机首屏可读状态”：只读展示、中文解释、无 raw ROS topic、无 robot state 发明、无主操作放行。

## Owner 和协作模式

- 主责：`full-stack-software-engineer`。负责 `mobile/web` 消费、展示、fixture、测试和 docs/product 同步。
- 协同：`robot-software-engineer`。只读核对 `TrashCollection.Feedback.current_step` 的阶段值、message、安全边界和 diagnostics/status 输入兼容；如确需轻量接口文档补充，由 Robot 在明确范围内处理。
- 收口：`product-okr-owner`。更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 与相关 process log；验收不把计划、UI mock 或 ACK 当业务结果。

## 明确不做

- 不继续 Objective 5 local metadata。
- 不继续 Objective 1 本地硬件 wrapper。
- 不新增真实硬件假设，不处理 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 不开放主操作，不发明 robot 状态，不声明真实手机、真实电梯、真实 Nav2/fixed-route、真实 dropoff/cancel completion 或 delivery success。

## 风险和阻塞

- 当前仍是 Docker/local `software_proof`，不是真实 iPhone/Android device behavior、production app 或真实 PWA prompt/user choice。
- 当前没有真实电梯、真实楼层确认、真实门状态、真实人工协助记录、真实 Nav2/fixed-route runtime、真实 task record/completion signal、WAVE ROVER/UART/HIL。
- 如果 Robot action feedback 未通过 operator gateway 或 mobile fixture 暴露，Full-Stack 必须 fail closed 显示“暂无实时电梯阶段”，不得从旧 summary 推断当前实时阶段。
