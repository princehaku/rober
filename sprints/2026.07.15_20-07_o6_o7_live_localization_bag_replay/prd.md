# PRD - O6/O7 Live Localization Bag Replay

## 问题与目标

O6/O7 仍缺真实机器人数据与真实回放/标注数据流。最近 `/scan` 和 camera live gate 都已安全失败并退役，
但最新 O3 现场材料证明定位 runtime 曾存在 `/tf`、`/amcl_pose` 等可读数据。本 sprint 以新的定位 topic 集合
产生 current-run rosbag/replay lineage，避免继续消费传感器 inventory blocker 或 support-only 包装。

## P0 验收口径

1. 唯一 inventory 来自 `root@192.168.1.11:37878`，使用 daemon-off/无 ROS CLI daemon 副作用的同 shell；
   只记录 allowlist topic 的 type/publisher 和 rosbag/storage/disk/conflict-recorder gate。
2. capture gate 必须证明至少一个动态定位 topic（`/odom` 或 `/amcl_pose`）publisher `>=1`，并证明 `/tf`
   publisher `>=1`；`/tf_static` 可选。任何必需 gate 不满足时 `live_capture_invocation_count=0`。
3. gate clean 后只录制一次，最长 `8s`，`--max-bag-size 16777216`，整个 bag 目录 `<=16 MiB`；禁止录制
   `/scan`、camera、command/control、credential 或非 allowlist topic。
4. 成功材料必须包含非空 DB3、metadata、DB3 SHA-256、每 topic type/message count、first/last timestamp、
   bounded replay JSONL，以及同一 `task_id` 的 sanitized manifest；不得保存 hostname、credential、绝对远端路径、
   raw message payload、stderr、traceback 或控制字段 true。
5. Algorithm 必须离线验证 metadata/DB3 可读、至少一个 TF 与一个动态定位 topic message count `>0`、时间范围有效、
   replay JSONL 与 manifest lineage 一致。
6. Full-stack 仅消费 Algorithm frozen manifest，沿既有 `POST /api/o6/archive/artifact-bundle`、archive task detail 与
   O7 consumer detail 读回相同 `task_id`、hash prefix、topic/message/timestamp counts 和 proof boundary；禁止新 endpoint。
7. 若 Algorithm 未形成 clean live manifest，Full-stack Phase C 必须 skip；不得用 fixture 宣称 live。

## 用户可见结果与失败语义

- 成功：O7 只读显示 `current_live_localization_bag_replay_ready_not_route_execution_proof`，包括 task、source、hash prefix、
  topic/count/time range、replay event count 与下一证据；不显示 raw payload 或路径。
- blocked：显示精确枚举 blocker，并保持 capture/consumer count；不生成空 DB3 或假 replay。
- 所有路径固定 `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、
  `safe_to_control=false`、`robot_control_executed=false`。

## 非目标

- 不修复 `/scan` 或 camera inventory；不写 topic、不发 `/initialpose`、不启停 runtime。
- 不运行 planner/controller/Nav2 route、不发运动/底盘/UART 命令。
- 不做 O5 tunnel/provider/public capture。
- 不以本地 fixture、mock bag、readback/export/browser/status wrapper 冒充 current-run live artifact。

## OKR 与 KR 决策

- O5 仍约 `85%`，但本轮因相同 blocker 已达两轮而暂停 provider lane。
- 目标 O6/O7 各约 `93%`；只有真实 bag + replay + same-task consumption 全部通过后，Product 才评估是否小幅上调。
- 规划阶段 KR `不归档`；route/delivery/HIL/safe-to-control 与 Mission Objective 0 不因本 sprint 自动达成。
