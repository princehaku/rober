# O6/O7 Route Bag Odometry Semantic Decoder PRD

## 需求目标

让 O6/O7 围绕同一 `task_id` 的 route bag DB3 进一步消费 `nav_msgs/msg/Odometry` 语义摘要，使 full semantic decode matrix 能把 Odometry topic/type 归类为 `decoded`，并让 PC/O7 可见该 decoder 覆盖。

## 用户价值

- 运营/研发人员可以从 O7 看到 route bag 中 Odometry 是否已被安全解析，而不是只看到 unsupported 计数。
- O6/O7 的数据链路从“知道有 payload”继续推进到“能解释更多路线/位姿相关 ROS payload”。
- 继续保持所有控制与成功声明关闭，避免把离线 decoder 覆盖误解为真实路线执行成功。

## 范围内

- Algorithm 增加 Odometry semantic summary：frame pair、位置样本、非零位移相关只读字段，复用已有安全 frame/id 和 CDR 解析边界。
- O6 更新 fixture/test/docs，证明 Odometry matrix item 可被安全归一和回读。
- O7 更新 fixture/test/docs，证明 Odometry decoded type 在 consumer detail、artifact bundle readiness 与 UI 中可见。
- 保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`live_nav2_run_proven=false`、`route_execution_success=false`。

## 范围外

- 不新增真实机器人控制、Nav2 执行、delivery 确认或 operator confirmation。
- 不新增 production cloud / DB / OSS / CDN / TLS / 4G 真实部署。
- 不输出 raw ROS payload、base64、完整 hash、绝对路径、credential URL、token 或 `/cmd_vel` 控制 topic。

## 验收口径

1. Algorithm 测试证明 Odometry 在 semantic replay 与 full semantic matrix 中进入 decoded 覆盖，并且 corrupt/unsafe Odometry fail-closed。
2. O6 测试证明 Odometry matrix item 在 archive detail、consumer detail 与 include 读回中保留 decoder label、counts、blocked reasons 和 false safety fields。
3. O7 测试证明 Odometry decoded item 在 consumer summary/UI 中可见，且 ready 语义只表示 local/offline semantic coverage。
4. 文档更新明确新增 decoder 覆盖和仍未证明的真实链路。
