# PRD - O3 Daemon/DDS Graph Split

## 用户价值

普通手机用户的一键送垃圾闭环依赖稳定定位、路径生成和路线执行。当前机器人还卡在 no-motion runtime graph 层：如果 ROS2 graph、daemon、DDS 或 lifecycle 可观测性不稳定，就无法可靠判断 AMCL、TF 和 planner 是否 ready，更不能安全进入 path generation 或 route execution。

本轮价值是减少现场调试盲区：把 `ros2_daemon_or_dds_graph_discovery_timeout` 拆成下一条可执行修复命令，而不是继续堆 helper wrapper。

## OKR 对齐

- O5 当前约 `85%`，是 `OKR.md` 4.1 当前最低 Objective，但 O5 需要真实 production/external evidence；当前环境没有公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic 或真实手机/browser 证据。
- 本轮不直接推进 O5，理由是继续做 O5 local/mock wrapper 已被硬 gate 判为 support-only，不能提升主 OKR。
- 本轮转向 O3/O1 no-motion runtime chain，目标是解锁 O1 缺口里的 current same-run path generation success 和后续 Nav2 route execution success。

## 范围

本轮只做只读 ROS2 graph/daemon/DDS/lifecycle 诊断和 helper 合同增强。

范围内：

- source-amortized graph probe 的 daemon/DDS 细分字段；
- daemon stop/start 或 daemon-safe retry 的只读摘要；
- `ROS_DOMAIN_ID`、`RMW_IMPLEMENTATION`、ROS/workspace 路径等安全 env 摘要；
- managed process lifecycle visibility 在 graph timeout 后的 remaining/excluded candidate；
- local fail-closed 和 true-board no-motion artifact。

范围外：

- 真实机器人运动；
- `/cmd_vel`、`/api/base/manual`、NavigateToPose；
- WAVE ROVER UART；
- O5 production cloud cutover；
- O6/O7 独立 UI/consumer surface；
- 将 diagnostic delta 计为 delivery/HIL/path success。

## 验收口径

Product 只接受以下结果之一：

1. 明确证明 daemon reset/no-daemon/DDS/domain/env 中至少一个候选被排除或保留，并写入 artifact 的 root-cause contract。
2. 明确证明 graph command budget 不足或 managed lifecycle visibility 是 primary/remaining blocker，并输出下一条 live command。
3. 如果 true-board 不可达，local artifact 必须 fail-closed，且 `tech-done.md` 写清无法证明 live state 的风险。

不接受：

- 只重复 `ros2_node_list_timeout`；
- 只重复 `ros2_daemon_or_dds_graph_discovery_timeout`；
- 只记录 helper partial/incomplete artifact；
- 没有 no-motion false fields；
- 把 no-motion diagnostic 说成 path generation、route execution、HIL、delivery 或 production success。

## 责任分工

- `robot-software-engineer`：实现、验证、修复、更新 `tech-done.md`。
- `product-okr-owner`：验收、OKR 判断、`side2side_check.md`、`final.md`、必要的 `OKR.md` 和 progress log。

## 成功判断

本轮即使不能上调 OKR 百分比，也应留下可复核的 live/root-cause artifact，并把下一轮从“graph timeout”推进到具体的 daemon、DDS、domain/env、lifecycle 或 budget 修复命令。
