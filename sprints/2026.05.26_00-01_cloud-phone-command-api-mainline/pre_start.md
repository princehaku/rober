# Cloud Phone Command API Mainline Pre-start

## sprint_type: epic

## CEO 原话

开始新一轮迭代, 用team继续完成OKR的完整实现。重心放在“功能往前走”，测试只当护栏用。优先推进OKR完成度低的部分。最后总结 OKR 进度并提交 git。

## 上轮状态

- `OKR.md` 4.1 显示 Objective 5 约 68%，是当前最低完成度 Objective。
- 最近多轮 O5 sprint 已反复完成 external evidence / review / handoff / escalation metadata，但未推动真实 phone -> cloud command enqueue 主功能。
- 本轮避免继续新增只读 wrapper，优先补一个可调用的 cloud phone command API 主链路。

## 本轮目标

把 cloud relay 从“已有机器人轮询 contract + 只读手机状态”推进到“手机/云端可提交任务级命令”：

- phone/API 提交 `collect`、`confirm_dropoff`、`cancel`。
- relay 将任务级命令规范化后写入现有 command queue。
- robot `remote_bridge` 继续通过 `/robots/{robot_id}/commands/next` outbound polling 领取。
- ACK/status 仍保持 fail-closed：命令入队、accepted、processing 都不等于 delivery success。

## Owner

- Product Manager / OKR Owner：sprint 留档、OKR 进度和收口。
- Robot Software Engineer：relay API、store 契约、单元护栏、cloud-relay 文档。
- User Touchpoint Full-Stack Engineer：手机同源入口和 PC workstation 任务级提交面，保持普通用户不接触 raw `/robots/*`。

## 风险边界

- 本轮不是公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、HIL、真实 Nav2/fixed-route 或 delivery success 证明。
- 本轮可以提升 O5 的软件功能完成度，但不能把 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 的真实现场边界改成 true。
- 命令提交必须是任务级 action，不得暴露 `/cmd_vel`、ROS topic、串口、WAVE ROVER、baudrate、凭证或本地路径。
