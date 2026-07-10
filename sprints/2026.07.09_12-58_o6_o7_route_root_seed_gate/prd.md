# O6/O7 Route Root Seed Gate PRD

## sprint_type: epic

## 产品问题

O7 当前是最低 active Objective（约 44%），需要继续证明 PC 端历史路线回放、标注和训练数据入口可以消费稳定的 O6 数据合同。O6 约 45%，已经有 offline artifact seed smoke，但 route-root seed 仍被 `route_bag` gate 牵制。

如果本地/Mock 路线目录已经具备 `route.csv`、manifest、derived replay 或可选 evidence/probe 摘要，却因为缺少 `route_bag` 而不能形成同一 `task_id` 的 seed smoke，O7 就无法稳定验证 route replay / labeling readiness。这个问题应该在 software proof 层先解决，而不是等待真实 rosbag、真实云或真实路线长期验收。

## 用户价值

- 运营调试人员可以先用本地/Mock route root 验证 O7 历史回放和标注入口，不被 `route_bag` 缺失卡住。
- O6 可以把 route root 材料归并成可查询摘要，作为后续真实路线材料接入前的稳定合同。
- 后续真实 `route_bag` 到位时，能作为增强证据接入，而不是改变 O6/O7 的基础消费路径。

## 需求范围

### 必须满足

- route-root seed local/mock smoke 不再强依赖 `route_bag` gate。
- 同一 `task_id` 下必须能表达 route root、manifest、derived replay、可选 evidence/probe 的摘要关系。
- 缺少 `route_bag` 时输出 blocked reason 或 next evidence，但不阻断 route-root seed smoke 本身。
- O7 consumer detail 必须以 fail-closed 方式展示 route-root seed readiness、blocked reasons 和 next required evidence。
- 所有控制、送达和安全相关旗标必须保持 false。

### 非目标

- 不实现真实生产云、真实 OSS/CDN、真实 annotation API 或真实 dataset export。
- 不证明真实机器人运动、真实底盘反馈、真实路线执行或 delivery success。
- 不读取任意绝对路径，不暴露 token、base64 媒体、原始大对象或串口/控制字段。
- 不改变 WAVE ROVER、ESP32、Orange Pi、UART 或硬件参数。

## 验收口径

本次文档创建阶段的验收只检查三个 planning docs 存在、关键词完整且 diff 无空白错误。

后续实现阶段的产品验收应满足：

- O6 有可回读的 route-root seed gate 摘要，明确 `route_bag` 是否存在、是否必需、缺失时的 blocked reason。
- O7 能消费该摘要并展示 route replay / labeling readiness 所需的最小信息。
- 危险字段、unsafe refs、缺失必需 route root 字段、schema mismatch 均 fail-closed。
- 证据边界写明为 local/mock software proof，不误报真实云、真实媒体或真实控制。

## safe flags false / 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false
