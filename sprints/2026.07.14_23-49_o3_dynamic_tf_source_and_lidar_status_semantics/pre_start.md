# Pre Start - O3 Dynamic TF Source and LiDAR Status Semantics

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/`
- Start window: 2026-07-14 23:49 Asia/Shanghai
- Product owner: `product-okr-owner`
- Parallel implementation owners: `robot-algorithm-engineer`, `robot-software-engineer`
- Integration owner: `robot-software-engineer`
- Planning status: ready for parallel implementation dispatch
- Execution boundary: strict no-motion, read-only runtime probes only

## 必读事实和上轮未完成项

本轮计划已复核 `AGENTS.md`、`OKR.md`、
`sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/{tech-done.md,side2side_check.md,final.md}`、
最近两轮 `final.md`，并按真实集成要求查阅 `docs/vendor/VENDOR_INDEX.md`。当前事实为：

- Objective 5 约 `85%`，仍是 `OKR.md` 4.1 的最低 Objective；但 14:38 CLI export、
  15:38 live relay HTTP 和 16:40 headless browser 均为 support-only，未产生 success-class
  production/cloud evidence。继续 relay/browser/export 会重复消费同一 external blocker。
- CEO 已提供真实上位机 `ssh root@192.168.1.11 -p 37878`，可推进新的 robot-runtime
  evidence class，而不是再生产 wrapper。
- 18:45 current-window strict no-motion run 已证明 fresh `/scan`、`/amcl_pose`、active
  map/AMCL、tf2 buffer `map->odom` 和 28-pose planner path；本轮不得重跑整套 planner wrapper。
- 上轮 exact gap 是
  `map_to_odom_dynamic_source_not_observed_in_tf_source_inventory`：tf2 buffer 可查到变换，
  但 `/tf` source inventory 未把 dynamic `map->odom` 与 publisher endpoint、source topic、
  timestamp/freshness 形成可验收关联。
- LiDAR current holder、ROS parameter 和递增 diagnostics 指向 `/dev/ttyACM0@150000`，但
  lifecycle `status` 的无参调用会合成默认 `230400`。`230400` 只能保留为 vendor/reference
  truth，不能覆盖 current runtime truth；该语义冲突尚未永久修复。

最近两轮 blocker 复核：16:40 的主 blocker 是缺 O5 production external success，18:45 的主
gap 是 dynamic TF source inventory。前者已连续被多种 support surface 消费，本轮切换到后者和
LiDAR status 语义修复，不再次消费 relay/browser/export。

## 用户价值和北极星

北极星仍是普通用户能发起一条可验证、可复盘、最终可送达的垃圾收集任务。本轮不把路径生成
本身包装成闭环，而是清除受控路线执行前的两个现场歧义：定位链能否证明当前 dynamic
`map->odom` 的真实发布来源，以及 operator/API 看到的 LiDAR baudrate 是否确为当前 holder
运行值。两个结果共同降低下一轮安全准入和 route execution evidence 的误判风险。

## OKR 映射和方向判断

- 本 sprint 走 O3 autonomous/navigation runtime lane，并支撑 O1 的 current localization/Nav2
  可信性；不直接计入 O5 production/cloud。
- 方向判断：`继续 O3 live evidence，但只关闭两个 exact gap`。暂停 planner、route readiness、
  relay、browser、export、handoff 和 readback wrapper。
- KR 决策：计划阶段不调整百分比、不归档 KR。只有 dynamic source attribution 和 current
  LiDAR status semantics 在真实板 current window 中通过，Product 才在 closeout 判断是否形成
  新证据增量；它们仍不等于 route execution、delivery、HIL 或 safe-to-control。
- 已完成 KR 历史位置不移动，继续保留在 `OKR.md` 历史区和
  `docs/process/okr_progress_log.md`；本轮没有可提前归档的 KR。

## 两条真实并行抓手

1. `robot-algorithm-engineer`：对现有 ROS graph 执行有界 `/tf` source inventory。只在必要时修
   `o10_amcl_nav2_runtime_proof.py` 和 targeted tests，使 current-window artifact 显式记录
   dynamic `map->odom` 的 publisher endpoint、`source_topic=/tf`、ROS timestamp 与 freshness。
   不启用 managed runtime、initialpose 或 path generation，不消费上一轮 28-pose planner 成功。
2. `robot-software-engineer`：修 `o1_lidar_lifecycle.sh status` 的 current/reference 分层，优先从
   当前 lifecycle holder argv、匹配 PID 的 persisted status、driver diagnostics 或显式 command
   推导 current runtime；无 current runtime 时 fail closed。`230400` 继续作为 vendor reference，
   `150000` 只有 current readback 支撑时才进入 current 字段。

两条工作流修改文件完全不重叠，初始实现和验证必须并行。Algorithm 只写
`artifacts/algorithm/**`；Robot Software 只写 `artifacts/robot_software/**`。两位 owner 返回后，
主节点再让 integration owner 汇总两份 owner report 并创建 `tech-done.md`。

## 安全和范围红线

本轮禁止 `/cmd_vel`、`/api/base/manual`、`NavigateToPose`、controller/BT、planner action、
LiDAR start/stop、WAVE ROVER UART、`/dev/ttyS5` 和任何非零底盘命令。允许只读 ROS graph、
`/tf`、lifecycle holder、status file、diagnostics 和 HTTP status readback；允许部署修复后的只读
collector/status 脚本，但不得重启底盘或 LiDAR lifecycle。

所有 current-window artifact 必须固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Epic 留档顺序与风险

计划阶段只创建 `pre_start.md -> prd.md -> tech-plan.md`。两 owner 完成并复验后才创建
`tech-done.md`；Product acceptance 后再按顺序创建 `side2side_check.md -> final.md`。本轮不得
预生成后续文档。

主要风险是 `/tf` 多 publisher 使 edge attribution 不唯一、AMCL graph discovery 抖动、TF
timestamp 与 wall clock 不同域、running PID/status file 漂移、diagnostics stale、SSH/Auth 失败，
以及远端脚本版本漂移。任何一项失败都必须落 current-window exact cause，不允许用历史 artifact
或 vendor reference 洗白 current truth。
