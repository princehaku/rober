# O6/O7 Route Delivery Closure Packet PRD

## 背景

O6/O7 已经具备 route bag evidence、payload replay、semantic replay、pose progress replay、Nav2 goal evidence、delivery result evidence 和 route execution result delivery readiness。当前缺口不再是继续扩展 decoder，而是把这些材料组织成更接近用户验收的“同一任务闭合证据包”。

## 用户价值

运营人员需要在 PC 端快速判断一个任务是否已经具备准现场验收材料：路线执行摘要是否存在、送达记录是否存在、人工确认是否存在、位姿进度是否能互相支撑，以及还缺哪条真实证据。该视图必须减少追日志成本，但不能制造“真实送达已完成”的错觉。

## 范围

本轮新增 `route_delivery_closure_packet` additive 合同：

- 输入：已有 Nav2 goal evidence、delivery result evidence、route execution result delivery readiness、route bag pose progress replay。
- 输出：同一 `task_id` 的闭合状态、linked evidence flags、blocked reasons、next required evidence、固定 false safety fields。
- O6：只存安全摘要，不回显原始路径、URL、token、payload 或可控制字段。
- O7：只展示闭合摘要和下一步 evidence，不启用提交、控制、发车或 success 标记。

## 非目标

- 不连接真实 production cloud、真实 DB/queue、OSS/CDN、TLS/4G。
- 不执行机器人控制、不发送 `/cmd_vel`、不证明真实 live Nav2 route execution。
- 不证明真实 delivery record、operator confirmation 或 delivery success 已在现场完成。
- 不归档任何 KR。

## 验收口径

- `route_delivery_closure_packet` ready 状态只能表示软件证据闭合，不得设置 `delivery_success=true`。
- 缺任一关键输入、schema mismatch、危险 true 字段、unsafe 文本或 task mismatch 都必须 blocked。
- O6/O7 能围绕同一 `task_id` 读回 closure packet，并给出清晰的下一步证据。
- sprint closeout 必须记录实际改动、验证输出、剩余风险和下一轮建议。
