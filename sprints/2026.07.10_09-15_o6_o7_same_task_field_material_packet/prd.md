# O6/O7 Same-Task Field Material Packet PRD

## 背景

当前 O1/O5/O6/O7 进度并列约 85%。最近一轮 hard gate 已明确：没有新的 live/field mission artifact delta 时，support-only 工作不能继续提高 O5/O6/O7 百分比。因此本轮产品需求不是新增一个显示面板，而是把已有准现场 route materials 作为可消费证据接入 Algorithm -> O6 -> O7 主路径。

## 用户价值

运营或开发人员需要在 PC/O7 task detail 中看到同一任务实际关联了哪些 mission materials：路线、关键帧、route bag / rosbag、replay。这样后续 CEO 或现场人员能按同一 `task_id` 补齐 delivery record、operator confirmation 或 live route execution，而不是在多个 wrapper 之间猜测哪个材料可用。

## 范围

本轮实现：

- 新增 `same_task_field_material_packet` 安全摘要，消费可复核的 route material 文件。
- O6 archive/readback 和 consumer detail 支持该 packet。
- O7 consumer/UI 展示该 packet，并使 checklist 能区分“准现场材料已消费”与“仍缺真实 delivery success”。
- 更新接口和导航/PC 文档，记录 proof boundary。

本轮不实现：

- 不连接真实 production cloud、OSS/CDN、production DB/queue。
- 不启动真实 Nav2、SLAM、底盘运动或 `/cmd_vel`。
- 不宣称真实 delivery success、真实 operator confirmation 或真实 live route execution。

## 验收标准

1. Algorithm manifest 中出现 `schema=trashbot.same_task_field_material_packet.v1`，并能识别至少 `route_csv`、keyframes、route bag / rosbag、replay JSONL 中的可用材料。
2. O6 readback 中出现 `schema=trashbot.o6.same_task_field_material_packet.v1`，并可通过 archive detail、field evidence、consumer detail 和 explicit include 回读。
3. O7 task detail 展示该 packet 的 status、present material types、sample refs、blocked reasons、next required evidence 和 false safety fields。
4. hostile/unsafe 输入必须 fail-closed，不回显敏感内容或 raw payload。
5. 本轮 OKR 只允许声明“准现场 same-task material consumption”进展；除非确有 live/field command execution，否则不得声明 delivery success。
