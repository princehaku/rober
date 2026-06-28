# PC Summary Current Fact Plain

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增 `current_fact_plain`。
- 字段由同一轮只读 `readback_summary` 和 `safe_command_boundary` 生成，合并：
  - 画面 WYSIWYG 状态
  - 地图/路线/雷达 marker WYSIWYG 状态
  - Nav2 路线执行复验状态
  - PC 键盘连续手控合同
  - 自由移动与建图 readiness
  - 最小发车前确认口径
- `failClosed` 连接失败分支也返回 `current_fact_plain`，避免外部脚本读到 null。
- 同步更新 App fixture、catalog summary 测试、README 和产品文档。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`
  - `Test Files 1 passed (1)`
  - `Tests 38 passed | 122 skipped (160)`
- 已通过：`npm --prefix pc-tools/workstation run build`
  - TypeScript、Vite client build、server TypeScript 均通过。
  - Vite 仍有既有 chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 375 passed (375)`
- 已重启 PC workstation API 到 `0.0.0.0:7001`，监听进程为 `node`。
- 已通过：只读验证 `/api/robot-control/summary.current_fact_plain`。
  - `current_fact_plain` 返回画面未可见且非独占、地图/路线/小车位置已显示、雷达旧来源点不贴图、Nav2 上次成功但 wheel L/R 未非零、键盘按住才动、自由移动可先启动、建图未 ready、发车前只复核安全确认。
  - `safe_to_control=false`
  - `safe_command_boundary.robot_control_executed=false`
  - `safe_command_boundary.nav2_goal_ready=true`

## 剩余风险

- 本轮只补 PC summary 只读事实字段，不额外请求上位机、不执行 Nav2、不启用键盘、不启动 free-roam、不发送 manual、delivery、stop 或 `/cmd_vel`。
- `current_fact_plain` 不覆盖 Vue 本地 pending 状态；页面仍由前端本地逻辑显示按钮按下后的临时状态。
- 未获得本轮现场安全确认前，不做真实运动、键盘连续手控、自由移动或自动驾驶执行验证。
