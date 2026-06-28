# sprint_type: micro

## 实际改动

- PC 普通“移动/导航”里的 `行程前确认` 文案新增 Nav2 managed runtime 说明。
- 当路线已准备、`nav2_goal_ready=true`，但 Nav2 stack/controller/planner 当前未运行时，普通首屏明确显示：
  - `执行会自动启动自动驾驶 runtime；执行接口只复核安全确认和固定白名单。`
- 这把“发车前预检最小化”和“自动驾驶服务当前停着但可由执行托管启动”拆开，避免现场误以为还要先做额外 Nav2 lifecycle 操作。
- 本轮只改普通 PC 文案和测试；没有触发 Nav2 goal execute、Nav2 start、底盘 manual、keyboard pulse、cmd_vel 或 delivery complete。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "lets a ready route execute through managed Nav2 runtime"`：通过，1 passed。
- `npm --prefix pc-tools/workstation test`：通过，367 passed。
- `npm --prefix pc-tools/workstation run build`：通过，Vite 仍提示现有 chunk 大于 500 kB 的非阻塞 warning。
- 只读 live `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`：通过，返回 `nav2_goal_ready=true`、`nav2_status=path_ready_with_service_blockers`、`nav2_stack_running=false`、`nav2_stack_lifecycle_state=stopped`、`planner_server_active=true`、`controller_server_active=false`、`path_generated=true`、`path_point_count=18`；`nav2_goal_next_action` 明确“用 ROS 重跑图上路线；执行时会自动启动自动驾驶 runtime”。上一轮执行结果仍是 `succeeded` 但 `goal_execution_base_feedback_lr_nonzero_proven=false`、`goal_execution_base_feedback_latest_raw_left=0`、`goal_execution_base_feedback_latest_raw_right=0`。

## 剩余风险

- 本轮没有现场安全确认，因此没有执行图上路线；完整 Nav2 路线仍未被本轮真实验证。
- live 仍显示上次路线 action 成功但执行窗口 wheel raw L/R=0/0，下一步需要现场安全确认后用 ROS 重跑图上路线，并确认同窗口 L/R 非零。
- 相机/雷达不是当前 Nav2 发车硬挡；它们仍分别影响画面所见即所得和建图 ready。
