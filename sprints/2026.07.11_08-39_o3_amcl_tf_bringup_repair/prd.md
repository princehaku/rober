# O3 AMCL TF Bringup Repair PRD

## 背景

O5 当前最低但缺真实 production external evidence，继续 support-only 工作不能计主 OKR 增量。O1/O6/O7 已有较高软件证据链，真正能解锁后续增量的是现场 O3 lane 产出同轮 localization/path material。

上轮真实板证据显示：

- `starts_nav2=true`
- `managed_runtime_started=true`
- `odom->base_link=true`
- `base_link->laser_frame=true`
- `nav2_amcl`、`nav2_map_server`、`nav2_lifecycle_manager` 包存在
- `/amcl_pose=false`
- `map->odom=false`
- `path_generated=false`

## 用户价值

普通手机用户最终只关心机器人能可靠沿固定路线送达。当前 AMCL/TF 未 ready 会阻断 fixed route、PC 地图位置、O6/O7 route material、后续 delivery proof。本轮优先修这一条现场主链路，而不是继续堆叠 support-only 摘要。

## 需求

1. 将 `/initialpose` 发布改成更稳定、可观测、可复核的 no-motion 方式，避免 `ros2 topic pub --once` CLI timeout 造成无法判断 AMCL 是否收到位姿。
2. 保留并增强 AMCL 输入和 TF root-cause 证据：AMCL 参数、publisher/subscriber、map/scan/topic inventory、`/tf` / `/tf_static` source、AMCL log tail。
3. 真实板可达时复跑 no-motion start/status/refresh/preflight，并把 artifact 写入本 sprint。
4. 如果 `map->odom` 成立，继续尝试 planner-only path generation；如果失败，必须输出 planner lifecycle/action/root-cause。

## 非目标

- 不做 O5 production readiness、O6/O7 archive/readback 或 PC UI surface。
- 不改 WAVE ROVER 运动控制默认值。
- 不执行真实运动、base manual、NavigateToPose goal 或 delivery task。
- 不把 historical/cross-run path 当作 same-run path success。

## 验收成功标准

- 本地验证通过：`py_compile`、targeted unit tests、scoped `git diff --check`。
- 真实板 artifact 至少证明本轮修复产生了新事实：`initialpose_published=true`、`amcl_pose_observed=true`、`map_to_odom=true`、`path_generated=true` 之一，或更细的新 blocker。
- 安全字段仍固定 false：`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

## OKR 映射

- 主映射：现场 O3 验证 lane，目标是从 AMCL/TF blocker 推进到 same-run path/material 前置证据。
- 间接映射：一旦产出 same-run path/material，可供 O1 localization/path bridge 与 O6/O7 live route material 消费。
- O5 不直接推进，理由是缺真实 external production evidence。
