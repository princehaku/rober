# O6/O7 Route Bag Semantic Replay PRD

## 用户价值

运营人员已经能看到 route bag DB3 的 topic/message/payload 摘要，但仍不知道这些 payload 是否能被安全解释成路线排障所需的 ROS 语义信息。本轮要让 PC/O6 在同一 `task_id` 下显示可解释的传感器语义摘要，帮助判断下一步要补 live Nav2、真实 delivery record，还是先修采集/回放数据。

## OKR 映射

- O6 KR2 / KR6：任务记录、事件/证据存档与 consumer read API 继续增强，从 payload hash 走到语义摘要回读。
- O7 KR3 / KR4：历史路线回放和数据标注工作台获得可读的 LaserScan/Image/TF 语义上下文，但仍不解锁真实控制。

## 范围

本轮做：

- 新增 `trashbot.route_bag_semantic_replay.v1` / `trashbot.o6.route_bag_semantic_replay.v1`。
- 从 DB3 白名单 topic type 派生 summary：
  - `sensor_msgs/msg/LaserScan`：样本数、range 样本长度、finite count、range min/max、angle min/max/increment 摘要。
  - `sensor_msgs/msg/Image`：样本数、width/height、encoding、step、data size 摘要。
  - `tf2_msgs/msg/TFMessage`：样本数、transform count、frame/child frame 安全样本摘要。
- O6/O7 只回显摘要字段、计数、blocked reasons、next required evidence 和 false safety flags。
- 更新相关 `docs/` 文档和 sprint 留档。

本轮不做：

- 不输出 raw payload、base64、完整 hash、绝对路径、credential URL 或图片内容。
- 不启动真实 ROS2 runtime，不依赖真实硬件，不连接 production cloud / OSS / CDN。
- 不声明 live Nav2 route execution、真实 robot motion、delivery record、operator confirmation 或 delivery success。

## 验收场景

- DB3 含 `/scan`、`/camera/image_raw`、`/tf_static` 时，Algorithm 生成语义摘要并嵌入 manifest 顶层和 `field_motion_evidence_packet`。
- O6 可从 field-evidence / artifact-bundle / consumer detail / `include=route_bag_semantic_replay` 回读摘要。
- O7 consumer detail 与 UI 显示 topic type、decode counts、LaserScan/Image/TF summary、blocked reasons 和 next evidence。
- 缺 DB3、坏 schema、未知 topic type、空 payload、危险 true、unsafe topic/text 时 fail closed。

## 验收命令

由对应 owner 子 agent 执行：

- Algorithm：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
- O6：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
- O7：`cd pc-tools/workstation && npm run test && npm run build && npm run lint`

## 风险边界

- Python 标准库语义解析只覆盖必要白名单字段，未知或不安全消息类型必须降级为 blocked/not decoded。
- 如果现场 DB3 payload 使用不兼容序列化或字段布局，本轮应输出 decode failed count 和 blocked reason，而不是猜测真实路线状态。
- 即使语义 replay ready，也仍是 software proof，不改变真实现场、生产云、OSS/CDN、annotation export 或 delivery success 缺口。
