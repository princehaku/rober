# O3 Nav2 Map AMCL TF Runtime Repair PRD

## 用户价值和产品北极星

用户价值不是再多一个 readback 面板，而是让真实板在不动车的情况下恢复定位与规划最小运行链，这样后续才有资格产出同轮路径、路线回放和送达证据。产品北极星仍是普通用户可安全、可验证地完成垃圾送达；本轮抓的是送达前最基础的定位 runtime 可用性。

## OKR 映射和方向判断

- O5 仍是当前最低主 Objective，约 `~85%`，但最近两轮 O5 收口已确认没有新的真实 production external evidence，继续 support-only 不产生主 OKR 增量。
- 本轮方向判断：**继续临时激活 O3 现场 lane**。
- 原因：真实板已可触达，且上一轮 live artifact 已把根因收敛到 `map_server_not_active`、`amcl_not_active`、`tf_missing`。这比继续消费 O5 blocker 更接近新的现场执行材料。
- 本轮不调整 `OKR.md` 百分比，不归档 KR；只有在拿到新的 runtime / path 现场证据后，后续 sprint 才考虑是否影响 O3/O1/O6/O7 的可消费材料链。

## 问题陈述

上一轮已经证明：

- LiDAR `/scan` 存在，不再是“传感器完全缺失”问题；
- map 文件存在，但 `/map` topic 没有真正建立；
- `/amcl_pose` 只有 topic type，没有 publisher；
- `map->odom` 与 `map->base_link` 都缺失；
- `/api/nav2/proof/refresh` 仍被 runtime blocker 卡住。

因此本轮不能再做 daemon/readback 包装，而是要修实际 runtime bringup。

## KR 拆解

- O3 现场 lane / runtime 前置 KR：
  1. 证明 no-motion Nav2 lifecycle start/status/refresh 调用链可复验；
  2. 证明 `/map_server`、`/amcl`、`/planner_server` 至少能被 lifecycle 读到 active/inactive/finalized 等明确状态，而不是 unavailable；
  3. 证明 `/map` 与 `/amcl_pose` 从“缺 publisher / 缺 topic”推进到新的现场事实；
  4. 证明 `map->odom` / `map->base_link` 中至少前一段 TF 开始出现，或把缺失根因缩小到更深层 launch/config/runtime 事实。

本轮无已完成 KR 可归档；历史区不移动内容。

## 本轮核心抓手

核心抓手是 **Robot Software owner 直接修 no-motion Nav2 runtime**，而不是再做 review、handoff、safe summary 或 wrapper。交付必须落在受管 lifecycle、launch/runtime 参数、proof refresh 和现场 artifact 上。

## 需要做什么

1. 审核 `o11_nav2_lifecycle.sh`、`upper_robot_api.py`、`autonomous.launch.py`、`o10_amcl_nav2_runtime_proof.py` 和 preflight 的 no-motion 调用链。
2. 找出为什么 `trashbot_map.yaml` 存在但 `/map_server` / `/amcl` / `/planner_server` lifecycle unavailable。
3. 修复 runtime 启动、参数透传、artifact 路径、lifecycle 等最小必要问题。
4. 复跑 local dry-run 与 live ssh no-motion preflight，生成本 sprint artifacts。
5. 同步更新导航文档，说明新的 runtime repair 边界和操作约束。

## 优先级和验收口径

- 优先级：P0。
- 最低验收通过线：
  - 本地静态检查和单测通过；
  - 真实板 `live_nav2_map_amcl_tf.raw.json` 产生新的 root cause 或更深层 runtime 事实；
  - 没有发送任何运动命令。
- 高价值验收：
  - `/map_server`、`/amcl`、`/planner_server` lifecycle 不再 unavailable；
  - `/map` 建立；
  - `/amcl_pose` 出现 publisher；
  - `map->odom=true`，并进一步带出 `map->base_link=true`；
  - `/api/nav2/proof/refresh` 不再停在上一轮同样的 timeout/root cause。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- 本轮不需要并行多 owner。若验证时暴露硬件串口或雷达物理接入问题，只记录为下一轮可能转给 `rober-hardware-engineer` 的 blocker，不在本轮 planning 内并行拆。

## 风险、阻塞和需要补齐的证据链

- 真实板虽然可达，但不保证 runtime 修复后就能立刻有 `path_generated=true`；本轮更现实的目标是先恢复 map / AMCL / TF。
- 若问题在 launch 配置之外，而是现场进程状态、板端文件漂移或 ROS2 运行环境漂移，本轮可能只会得到更深层 blocker。
- 需要补齐的证据链：
  - lifecycle readback
  - `/map` topic 事实
  - `/amcl_pose` publisher 事实
  - `map->odom` / `map->base_link` TF 事实
  - 同一轮 refresh readback

## 已完成 KR 的历史记录位置、证据来源和剩余风险

- 已完成 KR：无。
- 历史记录位置：本轮不移动 KR 到历史区。
- 证据来源：
  - `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/final.md`
  - `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/final.md`
  - `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`
- 剩余风险：即使本轮修通 no-motion runtime，也仍不等于 route execution success、delivery success、safe-to-control 或 HIL pass。

## 需要创建或更新的 sprint 文档

- 本轮创建并维护：
  - `pre_start.md`
  - `prd.md`
  - `tech-plan.md`
- 实施后必须由对应 owner 更新：
  - `tech-done.md`
  - `artifacts/**`
- 验收收口阶段必须补：
  - `side2side_check.md`
  - `final.md`
