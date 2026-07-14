# PRD - O3 Dynamic TF Source and LiDAR Status Semantics

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/`
- Product owner: `product-okr-owner`
- Parallel owners: `robot-algorithm-engineer`, `robot-software-engineer`
- Target: `root@192.168.1.11:37878`
- Product mode: current-window strict no-motion evidence plus semantics repair

## 问题定义

上一轮已经证明真实板能在 strict no-motion 条件下得到 fresh sensor/localization 和 28-pose
planner path，但留下两个会影响下一次现场决策的歧义：

1. `map_to_odom_dynamic_source_not_observed_in_tf_source_inventory`。tf2 buffer success 不能替代
   `/tf` dynamic source attribution；artifact 还缺 edge 对应的 publisher endpoint、source topic、
   timestamp/freshness。
2. LiDAR lifecycle bare `status` 会把默认 `230400` 合成到 running status，而 current holder 和
   diagnostics 是 `150000`。这会把 vendor/reference truth 混成 current runtime truth。

如果不先关闭这两个歧义，现场 owner 可能把 buffer 中的旧/不可归因 transform 当作 AMCL 当前
广播，也可能依据错误 baudrate 操作正在稳定运行的 lifecycle。本 sprint 要给出可机器验收的
当前事实，而不是再做 planner、状态面板或浏览器包装。

## 用户故事和北极星映射

作为现场 autonomy/operator owner，我需要在不让机器人运动、不 stop/start LiDAR 的前提下：

- 确认 current dynamic `map->odom` 是否来自可见的 `/tf` publisher endpoint，transform stamp
  是否可解析、是否 fresh；若无法唯一归因，得到精确 fail-closed 原因和候选端点；
- 确认 lifecycle/API 的 current baudrate 来自 running holder、匹配 PID 的状态、diagnostics 或
  explicit command，而 vendor reference `230400` 只出现在 reference 字段；
- 获得同一真实上位机窗口的原始 JSON、SHA、时间和 exit code，可供下一轮 route/HIL gate 复验。

这映射 O3 的定位/Nav2 可信性并支撑 O1；不证明用户任务已送达。北极星仍是可验证 delivery，
本轮只是把进入 route execution gate 前的 source/status 判断变得可信。

## 范围内

### Algorithm lane

- 对现有 ROS graph 做有界 `/tf` 与 `/amcl` endpoint/source inventory。
- 必要时修 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 和 targeted tests。
- 生成 `artifacts/algorithm/dynamic_tf_source_inventory.raw.json` 与 capture metadata/logs。
- Artifact 显式关联 `map->odom`、dynamic `/tf`、AMCL publisher endpoint、timestamp/freshness；
  attribution 不唯一时保留候选端点并 fail closed。
- 更新相关 navigation 文档，解释 attribution 和 freshness 边界。

### Robot Software lane

- 修 `onboard/scripts/o1_lidar_lifecycle.sh status`，避免 bare status 把 default/reference 当 current。
- 读取 running holder argv、PID-matched persisted status、driver diagnostics/explicit command 的
  current provenance；任何来源冲突都保留候选并 fail closed。
- 生成 `artifacts/robot_software/lidar_lifecycle_status.current.json` 和
  `radar_status.current.json`，证明 current `150000` 与 vendor reference `230400` 已分层。
- 更新 lifecycle tests 和 `docs/hardware/board_sensor_stack_smoke.md`。

## 范围外

- 重跑 `ComputePathToPose`、28-pose planner、fixed-route consumer 或 route readiness wrapper。
- `/cmd_vel`、`/api/base/manual`、`NavigateToPose`、controller/BT、真实路线运动。
- LiDAR start/stop、修改 baudrate/port、重启 lifecycle、抢占 `/dev/ttyACM0`。
- WAVE ROVER UART、`/dev/ttyS5`、底盘 firmware/launch/AMCL/Nav2 参数修改。
- O5 relay/browser/export、production cloud、delivery/operator acceptance、HIL 或 safe-to-control claim。

## Artifact Contract

Algorithm artifact 必须保留：

- target `192.168.1.11:37878`、remote hostname、capture timestamps、helper 双端 SHA 和 exit code；
- `collector_mode=read_only_existing_ros_graph_no_motion`；
- `path_generation_requested=false`、`path_generation_attempted=false`；
- `tf_readiness_summary.map_to_odom_dynamic.source_topic=/tf`；
- `dynamic_source_observed`、edge timestamp、freshness status；
- publisher attribution status、publisher endpoint（至少 node name、namespace、topic type、QoS）
  或无法归因的 exact cause/candidates；
- 全部固定 false safety fields。

Robot Software artifacts 必须保留：

- lifecycle running PID 与 holder provenance；
- current baudrate、`baudrate_readback_source`、`baudrate_readback_status`；
- `vendor_reference_baudrate=230400` 和独立的 reference-only classification；
- current `150000` 只能来自 current holder/status/diagnostics/explicit command；
- bare status 在无 running/current evidence 时 `baudrate=null`，不能回落到 `230400` current；
- API `GET /api/radar/status` 与 lifecycle current truth 一致；
- 全部固定 false safety fields。

## 优先级和验收口径

P0：保持 strict no-motion，不 start/stop lifecycle，不访问底盘 UART，不运行 planner。

P1：Algorithm current-window raw 能证明 dynamic `map->odom` 的 source topic、timestamp/freshness 和
publisher endpoint；若 DDS/graph 无法唯一归因，必须保守标记未通过并保留 candidates。

P1：Robot Software current-window status 把 `150000` current 与 `230400` reference 分开，且 bare
status 不再产生 synthetic current 值。

P2：两条 lane 均有 local tests、真实板只读验证、双端 SHA/exit code、失败定位和剩余风险。

## Product Acceptance

成功需要两条 lane 同时满足：

- Algorithm：current `/tf` sample 中出现 dynamic `map->odom`；`source_topic=/tf`；timestamp 可解析；
  freshness 不是 missing/stale；publisher attribution 至少能由 `/amcl` node graph 与 `/tf`
  endpoint inventory 一致归因。不能仅用 tf2 buffer transform success。
- Robot Software：running lifecycle current baudrate 为 `150000`，来源是 current evidence；
  `230400` 仅为 vendor/reference；API 与 lifecycle 输出一致，没有 synthetic current conflict。
- 所有控制、route、delivery、HIL 和 safe fields 为 false。

Fail-closed 允许 SSH、graph、timestamp、publisher attribution、holder/diagnostics 任一层失败，但
必须生成 current-window artifact，记录 target/time/exit/SHA、最窄原因和下一条只读复验命令。
不接受重新运行 planner、消费历史 artifact、把候选 publisher 写成已确认或把 vendor reference
写成 current。

## OKR/KR 收口规则

- 本轮最多接受为 O3/O1 current runtime evidence/semantics 增量；不自动上调百分比。
- 没有 route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 O5
  success-class production evidence，不归档 KR。
- 已完成 KR 历史位置不变；Product final 必须再次复核跳过 Objective 5 的 no-repeat 理由。
