# O6/O7 DiagnosticArray Semantic Decoder PRD

## 背景

O6/O7 现在可以消费 route bag payload、semantic replay、pose progress、execution readiness、full semantic decode matrix 和 Odometry decoder 覆盖。当前最低 active Objective 仍是 O6/O7。上一轮 O7 report 明确保留 `diagnostic_msgs/msg/DiagnosticArray` 为 unsupported，因此 operator 只能看到诊断 topic type 缺 decoder，不能看到诊断状态摘要。

## 用户价值

运营人员需要判断一次路线回放材料是否包含系统诊断、诊断等级和诊断来源。把 DiagnosticArray 转为安全摘要后，O7 可以在不泄露 raw payload、路径或凭证的前提下显示诊断消息是否可读、最高 level、status 名称样本和 key/value 数量，帮助定位 route bag 是否缺关键运行诊断。

## 范围

本 sprint 要求：

- Algorithm 支持 `diagnostic_msgs/msg/DiagnosticArray` 的 CDR 安全摘要 decoder。
- Full semantic decode matrix 对 DiagnosticArray 输出 `status=decoded`、`decoder_name=decode_diagnostic_array_payload`。
- O6 field evidence archive/readback/include 能保留 DiagnosticArray decoded item 和计数。
- O7 consumer/UI fixture 能展示 DiagnosticArray decoded coverage，并保持 unsupported/failed、blocked reasons、next evidence 和 false safety flags 的 fail-closed 语义。
- 文档同步更新 `docs/navigation/field_route_evidence_manifest.md`、`docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md` 或 `pc-tools/README.md` 中相关说明。

## 非目标

- 不实现所有 ROS message payload 全量解码。
- 不输出 DiagnosticArray 原始 message、raw payload、完整 key/value、base64、绝对路径、URL、token、credential 或 traceback。
- 不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery success 或 production OSS/CDN。
- 不开启任何控制动作或提交动作。

## 验收口径

- 至少一个算法测试证明 DiagnosticArray 在 semantic replay 和 full matrix 中进入 decoded coverage。
- 至少一个 O6 测试证明 O6 readback/include 保留 DiagnosticArray decoded matrix item。
- 至少一个 O7 测试证明 O7 consumer/UI 可读 DiagnosticArray decoded coverage。
- 所有相关 false safety flags 继续保持 false。
