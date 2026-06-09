# O7 Consumer Detail Route Replay PRD

## 1. 用户价值

PC 端运营调试平台的价值，不是把 fixture 看起来更完整，而是让操作员能够基于真实任务存档查看历史路线、事件链和证据链，快速判断“这次路到底怎么走的、在哪一步出问题、哪些证据能支撑复盘”。

O6 consumer detail 已经提供了任务列表与任务详情的统一读模型，本轮要把这份读模型真正接到 O7 route replay，让 route replay 不再停留在本地静态样本，而是变成面向真实任务存档的可复盘视图。

## 2. 本轮要解决的问题

1. 让操作员能够从 O7 入口直接进入某个任务的 route replay。
2. 让 route replay 读取同一份 O6 consumer detail，而不是再拼一套 fixture 数据。
3. 让历史回放、证据浏览、逐帧检查共享同一任务语义，减少后续 labeling / voice / safe command 的重复 join 成本。

## 3. 目标范围

本轮只做“route replay 真正消费 O6 consumer detail”的完整功能点，包括：

- 选择一个 consumer task 后进入 route replay。
- 显示任务摘要、trajectory frames、events、evidence refs、tunnel summary。
- 支持本地播放控制：上一帧、下一帧、重置、进度浏览。
- 保持 minimap / trajectory / state transition 的只读可视化。
- 保持 fail-closed 边界：缺 detail、缺 trajectory、unknown task、include/view 非法、blocked 状态都必须明确显示，不得伪造成功。

## 4. 非目标

- 不证明真实地图叠加、真实 ROS2 `/tf`、真实机器人运动或真实云生产接入。
- 不新增真实控制按钮，不下发 `/cmd_vel`，不做任何 robot ACK 成功宣称。
- 不把 fixture preview、local sample 或 mock data 伪装成生产回放成功。
- 不改写 O6 consumer read contract 本身，本轮只消费它。

## 5. KR 映射

| O7 KR | 本轮关系 | 说明 |
| --- | --- | --- |
| KR3 历史路线回放 | 直接推进 | 这是本轮唯一主目标 |
| KR4 数据标注 | 间接支撑 | route replay 复盘链为后续标注入口提供样板 |
| KR5 ASR/TTS | 间接支撑 | 统一 consumer detail 语义后可复用事件链结构 |
| KR6 手控/寻路 | 间接支撑 | safe command 后续需要同一 detail 语义做证据挂接 |

## 6. 验收标准

- O7 route replay 主路径不再依赖 fixture preview 作为首选数据源。
- 从 O7 入口可以加载 O6 consumer detail，并完成 route replay 的浏览与本地播放。
- route replay 只读消费 trajectory / events / evidence / tunnel，不产生新控制动作。
- 缺数据或 blocked 场景必须 fail closed，不能显示“真实回放成功”或“已控制机器人”。
- 相关 sprint 文档、产品文档和测试一起同步更新。
