# Cloud Phone Command API Mainline PRD

## 用户价值

普通用户最终应该通过手机发起“去送垃圾 / 确认投放 / 取消任务”，而不是复制 raw JSON、理解 `/robots/{robot_id}/commands` 或接触 ROS2。O5 当前最低，是因为云端链路有很多 proof 和只读状态，但缺少面向手机入口的真实任务级命令提交面。

## 产品目标

新增 `cloud_phone_command_api` 主链路：

1. 手机/同源 cloud API 可以提交 `collect`、`confirm_dropoff`、`cancel` 三类任务级命令。
2. API 返回安全 receipt，包含 command id、command type、queue sequence、ack 语义和 not delivery success 边界。
3. robot 侧仍沿用现有 outbound polling 与 ACK contract，不新增 inbound robot 控制。
4. 手机和 PC 工具可以展示“命令已入队/等待机器人处理”，但不能宣称送达、投放或取消完成。

## OKR 映射

- Objective 5 KR1：补齐 commands/status/ack contract 中 phone -> cloud commands 的可用入口。
- Objective 5 KR5：继续保持 bearer/env credential boundary，不把密钥或 raw Authorization 输出到 UI。
- Objective 5 KR6：网络或 ACK 未完成时 graceful degradation，不能把 pending/accepted 当 success。
- Objective 4 KR1/KR7：手机主操作从只读展示向真实任务级入口前进，但仍受 safety gate 控制。

## 非目标

- 不做公网部署、DNS、TLS、真实 4G/SIM 或 production DB/queue。
- 不做 OSS/CDN 上传或 live probe。
- 不做真实机器人运动、HIL、Nav2/fixed-route 或电梯现场验证。
- 不把按钮永远点亮；只有 API receipt 和 fail-closed 状态可以被展示。

## 验收口径

- relay 新增 phone-safe command API 能把三类任务级动作写入现有 command queue。
- focused tests 覆盖 collect、confirm_dropoff、cancel、bad action、auth failed、receipt not delivery success。
- mobile/web 或 PC workstation 至少一个用户触点能调用任务级 command API，而不是只读 wrapper。
- docs/product 和 docs/interfaces 同步说明新入口、字段语义、false-state 边界和剩余真实云缺口。
