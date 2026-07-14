# O3 AMCL TF Bringup Repair Pre Start

## sprint_type

sprint_type: epic

## 上轮未完成项

- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/` 已修复 `o11_nav2_lifecycle.sh start -> __run` runtime flag 透传，并让 `/api/nav2/proof/refresh` 在 `managed_runtime_started=true` 时回填顶层 `starts_nav2=true`。
- 同步到真实板后，`live_nav2_refresh_after_sync.raw.json` 证明 `starts_nav2=true` 与 `managed_runtime_started=true` 成立，但仍输出 `path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`。
- 当前 root cause 收敛到 `/amcl_pose_once_not_observed`、`map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom`。

## Blocker 扫描

- 最近 O5 sprint 已连续停在 `no_real_production_external_evidence`，继续 O5 readiness / probe / wrapper 默认 `okr_credit_allowed=false`，不能提升主 OKR。
- 最近 O3 sprint 不是重复消费同一 blocker：`05-55` 证明 `/scan` 已 observed；`06-37` 定位 Nav2/map/AMCL runtime 未 ready；`07-38` 修掉 managed runtime flag/readback 漂移。本轮接着修 AMCL/TF 直接根因。

## 本轮目标

在 no-motion 安全边界内修复 AMCL 初始化与 `map->odom` TF 发布链，使真实板 refresh 至少推进到：

- `/initialpose` publish 成功且可被 AMCL 消费，或输出比 CLI timeout 更具体的失败原因；
- `/amcl_pose` observed，或输出 AMCL 参数、订阅、日志、map/scan/TF 输入层的新 blocker；
- `map->odom` observed，或输出 AMCL 不广播该 TF 的明确根因；
- 若上述成立，则继续尝试 no-motion path generation，目标是 `path_generated=true` 或结构化 planner blocker。

## Owner

- `robot-algorithm-engineer` 单线闭环：实现 AMCL/TF bringup repair，运行本地与真实板 no-motion 验证，更新 `tech-done.md` 和 artifacts。
- 主节点：只做计划、派单、验收、`side2side_check.md` / `final.md` 汇总。

## 验收口径

- 不发送 `/cmd_vel`，不调用 `/api/base/manual`，不执行 NavigateToPose goal。
- 允许 no-motion `/initialpose`、managed map/AMCL/planner runtime 和 ComputePathToPose planner-only opt-in。
- 若真实板仍 fail-closed，必须把 blocker 下钻到 AMCL 输入、initialpose 发布、map topic、TF source 或 planner lifecycle 之一。
