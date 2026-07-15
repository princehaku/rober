# Pre-start - O6/O7 Live Localization Bag Replay

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_20-07_o6_o7_live_localization_bag_replay/`
- Start：`2026-07-15 20:07 Asia/Shanghai`
- Primary owner：`robot-algorithm-engineer`
- Conditional consumer owner：`full-stack-software-engineer`

## 用户价值与北极星

本轮服务需要判断真实机器人定位数据是否可以被回放、存档和运营消费的研发/运营人员。北极星不是新增
preflight、readback、状态页或 fixture，而是从 `root@192.168.1.11:37878` 已存在的 ROS2 publisher 得到一份
本轮新产生、可校验、可离线回放的 localization rosbag，并让 O6/O7 沿同一 `task_id` 消费真实
source/hash/topic/message/timestamp lineage。

## 上轮未完成与 anti-repeat

- O5 约 `85%` 最低，但 `2026.07.15_09-04` 与 `2026.07.15_10-00` 已连续两轮消费
  `provider_runtime_preflight`；本轮按 blocker 红线切换 Objective，不做第三轮 O5 wrapper、诊断或 live 重跑。
- O6/O7 各约 `93%`，是最低可行动 Objective。
- `2026.07.15_10-59` 的 `/scan` inventory/capture gate 已消费并退役；本轮不得依赖或重跑 `/scan`。
- `2026.07.15_11-58` 的 camera inventory/keyframe gate 已消费并退役；本轮不得依赖或重跑 camera。
- 不重复 map/route/readiness/export/browser/voice/packet/mock-only wrapper；没有新 DB3 与 replay lineage 就不计 mission input。

## 本轮抓手与 owner 路由

1. `robot-algorithm-engineer` 先做一次 daemon-off、只读 publisher/runtime gate；gate clean 后只允许一次有界
   rosbag capture，allowlist 为 `/tf`、`/tf_static`、`/odom`、`/amcl_pose`，实际录制可按 publisher 情况裁减，
   但必须包含至少一个动态定位 topic 和 TF。
2. Algorithm 生成真实 DB3、metadata、SHA-256、sanitized manifest 与 replay JSONL，并完成离线回放/结构验证。
3. 只有 Algorithm 输出 frozen live manifest 且 gate clean，`full-stack-software-engineer` 才进入 Phase C，复用既有
   O6 artifact-bundle/task-detail 与 O7 consumer-detail；不得新增 endpoint。
4. Algorithm blocked 时 Full-stack 必须 `skip`；禁止以 fixture、mock manifest 或相邻 wrapper代替真实 bag。

## 安全边界与升级条件

- 全程 strict no-motion/read-only：不发布 ROS topic，不写 `/initialpose`，不启停或重启现有 runtime，不启动 launch，
  不调用 planner/controller/NavigateToPose，不写 `/cmd_vel`、`/api/base/manual` 或 UART。
- inventory invocation 最多 `1`；live capture invocation 最多 `1`。任一步失败即 fail closed 并收口，不重跑 SSH、
  inventory 或 record。
- 固定 `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、
  `robot_control_executed=false`、`user_action_delta=false`、`live_control_delta=false`。
- 本轮最多形成 `credit_tier=mission_input`；不等于 route execution、delivery、HIL 或 Mission Objective 0 完成。
