# Pre Start - O3 CLI Full Path Pose Export

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/`
- Automation run: `rober-okr`
- Started at: `2026-07-13 02:00 +08:00`
- Primary owner: `robot-algorithm-engineer`
- Product acceptance owner: `product-okr-owner`

## 上轮未完成项和最新阻塞

上一轮 `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/` 已把 00:00 route-intent packet 消费到 fixed-route consumer dry-run，并记录：

- `validation_status=pass_with_material_boundary`
- `dry_run_status=accepted_partial_material_dry_run`
- `authoritative_path_point_count=21`
- `materialized_stdout_tail_pose_count=14`
- `minimum_unmaterialized_path_pose_count=7`
- `blocked_reason=full_structured_path_poses_missing`

该 blocker 不是 O5 的 production external evidence blocker，也不是重复包装 consumer dry-run；它是 O3/O1 fixed-route lane 的下一层 helper/export blocker：CLI fallback 目前只持久化 `path_point_count` 和 `stdout_tail`，没有把 ComputePathToPose 的 full structured poses 写入 artifact。

## 本轮目标

本轮目标是让 no-motion ComputePathToPose CLI fallback 在成功生成 path 时，解析并持久化 structured path poses 或明确给出无法从旧 artifact 追溯 full poses 的窄 blocker。

验收边界：

- 允许改 helper/export、单测、fixed-route 文档和本 sprint 留档/artifact。
- 继续 strict no-motion。
- 不运行 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不声明 route execution、delivery、HIL、safe-to-control 或 production external evidence。

## Owner 路由

- `robot-algorithm-engineer`：实现 CLI stdout path pose parser/export，补单测，生成本 sprint artifacts 并更新 `tech-done.md`。
- `product-okr-owner`：实现完成后做 acceptance wording、OKR 边界和 closeout。
- `robot-software-engineer`：仅当 Algorithm 证明 helper 接口边界需要 ROS2 主链路支持时介入；本轮默认不派。
- Hardware / Full-stack：本轮不涉及。

## 重复 blocker 核对

最近两轮的主要 blocker 是：

- 00:00：source artifact 只有 partial stdout-tail route-intent material。
- 01:00：consumer dry-run 可消费 partial material，但不能 claim full 21-point replay，阻塞在 `full_structured_path_poses_missing`。

本轮不再重复生成 route-intent 或 consumer dry-run，而是修/验 CLI fallback structured export。因此不是第三次消费同一包装层；若实现证明旧 source artifact 已无法追溯 full poses，则 final 必须把下一步缩窄为重新跑 live no-motion capture 以产出新 structured artifact。
