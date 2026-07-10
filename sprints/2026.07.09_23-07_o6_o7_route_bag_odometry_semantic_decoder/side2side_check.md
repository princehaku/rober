# O6/O7 Route Bag Odometry Semantic Decoder Side-by-side Check

## 验收目标

对照 `prd.md` 和 `tech-plan.md`，本轮目标是把 `nav_msgs/msg/Odometry` 从 route bag semantic coverage 的缺口推进为 decoded evidence，并在 O6/O7 回读展示中保持 fail-closed。

## 对照结果

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Algorithm 输出 Odometry semantic decoder | 通过 | `algorithm_worker_report.md` 记录新增 `decode_odometry_payload`、`odometry_summary` 和 full matrix decoded item；验证 `Ran 48 tests in 0.275s OK` |
| O6 回读保留 Odometry decoded item | 通过 | `o6_worker_report.md` 记录 O6 fixture/断言覆盖 `nav_msgs.msg.Odometry`、`decoder=decode_odometry_payload`、counts 和 include 回读；验证 `Ran 163 tests in 60.247s OK` |
| O7 UI/consumer 展示 Odometry decoded coverage | 通过 | `o7_worker_report.md` 记录 `semantic_topic_types` 包含 Odometry，`/odom` matrix item 为 decoded，coverage ratio 为 `0.75`；验证 `482 passed`、build、lint 通过 |
| 安全字段保持 false | 通过 | 三条 worker report 均记录 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 口径 |
| 不重复消费 production/live blocker | 通过 | 本轮只扩展 decoder 覆盖，不声称真实 cloud、live Nav2、delivery result 或 operator confirmation |

## OKR 影响

- O6：约 74% -> 约 76%。
- O7：约 74% -> 约 76%。
- 不归档 KR。

保守上调理由：本轮不是新增 wrapper，而是把上一轮 matrix 中“继续补安全 ROS message decoder”的下一步落成 Odometry decoded coverage，并贯通 Algorithm -> O6 -> O7 验证；但真实生产链路和真实送达链路仍未证明。

## 剩余风险复核

- 仍缺真实 production cloud、真实隧道、生产 DB/queue、OSS、TLS/4G、真实机器人数据和生产级查询容量。
- 仍缺真实 live Nav2 route execution、真实 delivery record、operator confirmation、delivery success 和长期路线验收。
- raw ROS message payload 仍未全量语义回放；后续应继续把 unsupported topic type 转为 decoded evidence。
