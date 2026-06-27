# 2026.06.28 03:52 PC Nav2 Plain Language Summary

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts` 把 PC summary 中 Nav2 服务类中文状态改成普通用户口径：
  - `Nav2 服务未启动` -> `自动驾驶服务未启动`
  - `Nav2 planner` -> `规划服务`
  - `Nav2 controller` -> `控制服务`
- blocker id 保持不变，仍为 `nav2_stack_not_running`、`planner_server_inactive`、`controller_server_inactive`，方便自动化和高级诊断稳定判断。
- `pc-tools/workstation/src/shared/contracts.ts` 同步更新 `nav2_goal_label` union。
- `pc-tools/workstation/test/catalog.test.ts` 更新对应断言，锁定“启动自动驾驶服务（不发车）/恢复规划服务/恢复控制服务”的普通口径。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md`。

## 验证结果

- `npm test` 通过，335 个测试通过。
- `npm run lint` 通过。
- `npm run build` 通过。
- `git diff --check` 通过。
- live 重启 `0.0.0.0:7001` 后，`/api/robot-control/summary` 返回：
  - `nav2_goal_label=自动驾驶服务未启动`
  - `nav2_goal_next_action` 包含 `先启动自动驾驶服务（不发车）`
  - blocker id 保持 `nav2_stack_not_running,path_generation_not_observed,path_point_count_not_positive,robot_map_pose_not_observed`

## 剩余风险

- 本轮只修正 PC summary 文案，不启动 Nav2、不发送 NavigateToPose、不发送 manual、keyboard、free-roam、stop 或 `/cmd_vel`。
- live 车端仍显示 Nav2 stack stopped；没有现场安全确认前不执行启动或路线重跑。
