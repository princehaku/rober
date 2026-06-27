# 2026-06-27 15:43 PC Nav2 latest no-motion boundary

## sprint_type: micro

## 设计结论

本轮继续推进“完整 Nav2 路线执行”和普通首屏 WYSIWYG 安全口径。live 状态显示：

- `GET /api/robot-control/nav2/goal/execution/latest` 是只读 latest 查询。
- 该响应顶层 `robot_control_executed=true`，但这只是历史 artifact 记录“上一次 Nav2 执行发过底盘命令”。
- 顶层字段容易被误读成“本次刷新 latest 重新发车”。

正确口径：

- latest GET 顶层 `robot_control_executed` 表示本次 PC 请求是否执行动作，必须固定为 `false`。
- 最近一次真实行程是否执行过底盘命令，继续保留在
  `goal_execution_key_values.robot_control_executed`、`sends_base_motion_commands`、
  `base_command_mode` 和 wheel raw L/R 证据里。
- `POST /api/robot-control/nav2/goal/execute` 的本次执行响应不变；真正执行成功时顶层仍可反映本次动作。

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/nav2/goal/execution/latest` 响应顶层 `robot_control_executed` 固定为 `false`。
  - 删除 latest handler 中不再需要的 `latestResult` 临时变量。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 latest GET 回归：历史 `goal_execution_key_values.robot_control_executed=true` 保留，但顶层为 `false`。
  - 保持 Nav2 execute POST 回归：执行转发成功时顶层 `robot_control_executed=true`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 latest GET 顶层 no-motion 边界和历史行程证据字段位置。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "Nav2 goal execution reuses|Nav2 latest execution proxy"`
  - `Tests 4 passed | 124 skipped`
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Tests 295 passed`
- 已通过：`npm --prefix pc-tools/workstation run build`
  - 保留既有 Vite chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation run lint`
- 已通过：`git diff --check`

## Live 只读验证

- PC Node 已重启并监听 `0.0.0.0:7001`。
- `GET /api/robot-control/nav2/goal/execution/latest?baseUrl=http://192.168.1.11:8787` 返回：
  - `proxy_status=latest_loaded`
  - 顶层 `robot_control_executed=false`
  - `goal_execution_key_values.robot_control_executed=true`
  - `goal_execution_key_values.status=goal_succeeded`
  - `goal_execution_key_values.base_feedback_lr_nonzero_proven=false`
  - `goal_execution_key_values.base_command_mode=pwm`
  - `safe_to_control=false`
  - `delivery_success=false`
- summary 仍正确提示：上次 action 成功但 wheel raw L/R 未非零，下一步用 ROS 重跑图上路线。

## 剩余风险

- 当前 live Nav2 仍未证明完整路线执行：wheel raw L/R 同窗口还是 `0/0`，需要 operator 勾选行程前安全确认后重跑 ROS 路线。
- 本轮没有执行 Nav2、manual、keyboard、free-roam、delivery 或 `/cmd_vel`；只修正 latest GET 的 no-motion WYSIWYG 边界。
