# 2026.07.13 03:00 O3 live full structured path capture - PRD

## 用户价值

普通用户需要的是可验证路线能力，而不是又一层包装材料。上一轮已经证明 helper 可以导出 structured path poses，但旧 live artifact 只有 14 个完整 stdout-tail pose。本轮要把缺口转成同轮 live structured material：在 strict no-motion 条件下重新捕获 planner-only path，并持久化完整 path poses。

## 需求

1. 使用更新后的 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 执行 strict no-motion `ComputePathToPose` live capture。
2. 产出新的算法 artifact 和 summary，优先证明：
   - `path_generated=true`
   - `path_point_count=21`
   - `path_structured_pose_count=21`
   - `path_structured_poses` 与 preview 字段持久化
3. 如果现场 runtime 不能产出 21 个 structured poses，必须 fail-closed 写清新 blocker，不得回退为历史材料包装。
4. 保持 no-motion 安全边界，所有 motion/control/delivery/HIL/safe-to-control 字段必须 false。

## 验收标准

- 新 artifact schema 和关键字段可由 JSON 检查验证。
- 新 artifact 必须是本轮 live capture 结果，而不是直接复用旧 21:57 artifact。
- `path_structured_pose_count=21` 时，只能接受为 O3/O1 strict no-motion full structured planner path material。
- 若无法达到 21，接受条件是 blocker 比 `historic_stdout_tail_truncated_full_pose_replay_unavailable` 更窄且来自本轮 capture。
- 不允许声明 route execution、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery、HIL、safe-to-control 或 production success。

## 非目标

- 不执行 fixed-route movement。
- 不启动 delivery task。
- 不修 O5 production/external evidence。
- 不把 helper readiness、历史材料、readback-only 或 checklist-only 计为 KR 完成。
