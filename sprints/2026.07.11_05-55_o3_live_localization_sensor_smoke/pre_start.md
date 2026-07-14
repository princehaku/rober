# O3 Live Localization Sensor Smoke

## sprint_type

sprint_type: epic

## 背景

`OKR.md` 4.1 当前最低 Objective 仍是 O5，约 `~85%`。但最近两轮 sprint 已经把“继续做 O5 / O1 support-only 变体没有新增 mission delta”这件事说明得足够清楚：

- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/final.md` 已证明当前环境没有新的真实 O5 external production evidence，也没有新的 field execution material；继续 O5 readiness、probe、wrapper、support packet 或 checklist 只会重复消费同一 blocker，并保持 `okr_credit_allowed=false`。
- `sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/final.md` 已证明真实上位机 SSH/API 可达，但当前 no-motion `/api/nav2/proof/refresh` fail-closed 卡在 `/scan_once_not_observed`、`/amcl_pose_once_not_observed`、`map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom` 和 `localization_not_ready_for_path_generation`。

因此本轮不能再继续 O5/O1 wrapper、readback、historical comparator 或 support-only lane，而要把下一步改成真实上位机 live localization/sensor smoke：先确认当前同窗 `/scan`、`/amcl_pose`、`/tf map->odom`、`/tf map->base_link` 是否 ready，再重跑 no-motion `/api/nav2/proof/refresh`。

## 用户价值和北极星

用户现在需要的是一条能直接解锁下一条现场执行命令的最小证据链，而不是更多“为什么还不能动”的外层包装。北极星仍然是让机器人可复验地完成现场路线与投递闭环；本轮只负责把 O3 的定位前置条件压缩到一个真实上位机 no-motion smoke 任务，让后续 route/path 证明不再停留在历史 latest 或 support-only 解释层。

## 本轮目标

创建一个可执行的 epic 计划，要求对应 Engineer 在真实上位机 no-motion 场景下完成以下顺序：

1. 同窗检查 `/scan` 是否可观测；
2. 同窗检查 `/amcl_pose` 是否可观测；
3. 同窗检查 `/tf map->odom` 是否存在；
4. 同窗检查 `/tf map->base_link` 是否存在；
5. 仅在上述定位链基本 ready 时，重跑 `/api/nav2/proof/refresh`；
6. 无论结果成功还是 fail-closed，都输出新的 blocker 分层或新的 no-motion proof summary。

本轮目标只包括：

- live no-motion localization / sensor smoke；
- no-motion `/api/nav2/proof/refresh` 重跑；
- 当前同窗 blocker 收敛；
- 下一条现场执行命令定义。

本轮目标不包括：

- 底盘运动；
- `/cmd_vel`；
- `/api/base/manual`；
- Nav2 `NavigateToPose`；
- delivery success；
- `safe_to_control=true`；
- `hil_pass=true`。

## Owner

- 主责任 Engineer：`robot-software-engineer`
- 条件咨询：`rober-hardware-engineer`（仅当 `/scan` 缺失需要核对真实传感器/串口/驱动 bringup 事实时）
- 条件咨询：`robot-algorithm-engineer`（仅当 `/api/nav2/proof/refresh` 返回需要解释 path/localization blocker 时）
- Product closeout：主节点汇总，不在本轮预先改 `OKR.md`

## 验收口径

- 必须创建 `pre_start.md`、`prd.md`、`tech-plan.md` 三份 epic 计划文档。
- `tech-plan.md` 必须包含 `OKR 最低优先级核对`，并明确解释为何本轮不继续 O5/O1 support-only。
- 计划必须明确写出同窗 smoke 目标：`/scan`、`/amcl_pose`、`/tf map->odom`、`/tf map->base_link` 与 `/api/nav2/proof/refresh`。
- 计划必须明确禁止任何运动和控制接口：`/cmd_vel`、`/api/base/manual`、`NavigateToPose`、真实底盘运动。
- 计划必须把 proof boundary 固定为 no-motion localization smoke，不允许把 smoke 结果包装成 route execution、delivery 或 safe-to-control 结论。

## 风险与阻塞

- 当前最大风险不是 SSH/API 不通，而是定位前置条件虽然部分可达，但 live `/scan`、`/amcl_pose`、TF 链仍未 ready，导致 refresh 永远卡在 localization blocker。
- 若 `/scan` 缺失，问题可能落在雷达供电、驱动、launch、topic remap 或上位机传感器 bringup 链；本轮只能做 no-motion smoke 分层，不能假装已完成硬件集成。
- 若 `/amcl_pose`、`map->odom` 或 `map->base_link` 缺失，本轮要把 blocker 收敛到 localization/map/TF 发布链，而不是继续读取旧 latest 或继续做 O5/O1 旁路材料。
