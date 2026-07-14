# Product Requirements Document

- `sprint_type: epic`
- 状态：需求冻结，等待 `robot-algorithm-engineer` 单线实施。
- 目标：在 `root@192.168.1.11:37878` 完成 current live strict-no-motion controlled initialpose localization proof。

## 用户问题与核心抓手

上一轮已经恢复 localization-only runtime，但 AMCL 未获得初值，因此没有 current `/amcl_pose` 与 dynamic `map->odom`。本轮核心抓手不是再做 readiness wrapper，而是先审计 persisted pose live consumption；若确实未消费，则以 canonical map 中可证明为 free 的像素转换出 world pose，并在所有 pre-write gate clean 后最多一次发布 `/initialpose`。

## 功能需求

### 1. Persisted pose 审计

- 记录 repo config、helper 生成参数、runtime effective AMCL params、AMCL startup log 与发布前 live 输出的来源差异。
- 上一轮 helper 临时参数 `set_initial_pose: false` 必须显式进入审计。
- config 中存在 `set_initial_pose: true` 只算静态配置事实，不算 live consumption。
- 只有发布前已经获得 fresh `/amcl_pose`，且同窗口存在 AMCL 唯一 dynamic `map->odom` endpoint/publisher/header timestamp/freshness，才可判定 persisted pose 已 live 消费；此时必须跳过 `/initialpose`。

### 2. Canonical map free-cell/world pose 审计

- 重新按 helper canonical ranking 核对当前 map；上一轮唯一 top 为 `/root/rober/onboard/runtime/maps/trashbot_map.yaml`、free cells `425`，本轮不得仅复用旧结论。
- artifact 必须记录 YAML/PGM 路径与 SHA、宽高、resolution、origin、mode/threshold、free pixel row/column/value、图像坐标到 map world 坐标的换算、最终 `x/y/yaw/frame_id=map`。
- 选点必须是确定性的 canonical free cell；任一字段不可解析、像素非 free、world pose 越界或 map 排名不唯一时 fail-closed，不得发布。

### 3. 发布前 gate

- map_server 与 AMCL lifecycle active。
- `/scan` 必须同窗口 sample fresh。
- AMCL `/initialpose` subscriber 必须 active 且归属清楚。
- TF authority 必须清楚：禁止 static `map->odom`，禁止竞争 dynamic `map->odom`；AMCL 是本轮唯一允许形成该 dynamic edge 的 authority，既有 `odom->base_link` 与 static TF 来源需可解释。
- persisted pose、canonical pose、subscriber、TF authority 任一未 clean，`initialpose_publish_attempted=false`。

### 4. 单次 `/initialpose`

- 仅在发布前 gate 全部通过且 persisted pose 未 live 消费时允许执行。
- 实际 ROS publish attempt 总数必须 `<=1`；不能把 rclpy burst 多条消息或 CLI fallback 叠加包装成“一次”。
- 若一次已发出，不论后续是否观测到结果，都不得重发；必须直接进入 read-only post-write capture 或 fail-closed。

### 5. 发布后 clean gate

- `/scan` 与 `/amcl_pose` 必须同窗口 fresh，并记录 header timestamp 与 wall-clock freshness。
- dynamic `map->odom` 必须唯一归属 AMCL，记录 endpoint、publisher、parent/child、header timestamp 与 freshness；静态 edge 不接受。
- helper 自有 process group 必须 cleanup clean、residual `0`，既有进程保持。
- artifact 与 `tech-done.md` 必须固定：`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`robot_control_executed=false`。

## 验收与拒绝口径

- Clean acceptance 需要 persisted audit、canonical pose audit、pre-write gate、attempt `<=1`、post-write freshness、唯一 AMCL dynamic TF 与 cleanup 全部通过。
- 若 persisted pose 已 live 消费，可以 `initialpose_publish_attempted=false` 收口，但仍必须满足同一 clean post-read gate。
- 仅 endpoint 可见、旧 `/amcl_pose`、无 timestamp 的 TF、静态 TF、config readback、AMCL active 或 map 可读均不能单独验收。
- 本轮不证明定位精度、机器人真实物理位姿、path、route execution、delivery/operator acceptance、HIL 或 safe-to-control。

## 风险与证据缺口

- canonical free cell 只证明种子在地图 free 栅格，不证明机器人真实物理位置与该种子一致。
- AMCL 可能接收一次初值后仍不输出 fresh pose/TF；此时不得重发，只能记录 exact blocker。
- 现有 helper 的 rclpy burst/CLI fallback 可能超过一次，必须先修成全路径总 attempt `<=1` 并用单测锁定。
- TF source collector 或 ROS graph CLI 可能 timeout；不得用 lifecycle log 覆盖 endpoint/timestamp/freshness 缺口。
