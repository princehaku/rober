# PC Nav2 plain hint user words

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`readback_summary.nav2.plain_hint` 合成前新增普通用户口径转换，把 `wheel raw L/R` 转成 `执行窗口轮速 L/R`，把 `Nav2 planner/controller` 转成 `规划服务/控制服务`。
- `pc-tools/workstation/test/catalog.test.ts`：补 `nav2.plain_hint` 不再包含 `wheel raw` 的断言，同时保留拆分诊断字段里的高级术语。
- `docs/product/pc_tools_workstation.md`：同步记录 `nav2.plain_hint` 的用户口径和只读边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`，`1 passed`，`38 passed | 122 skipped`。
- 已通过：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 均成功；仅保留既有 chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation test`，`2 passed`，`375 passed`。
- 已通过：重启 PC API 到 `0.0.0.0:7001`，`lsof` 显示 `node` PID `50053` 监听 `TCP *:7001`。
- 已通过：只读请求 `GET /api/robot-control/summary`，live `readback_summary.nav2.plain_hint` 返回 `上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或控制服务。下一步：勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。`，不含 `wheel raw`；拆分诊断字段仍保留 `goal_execution_wheel_raw_lr_*` 原术语。

## 剩余风险

- 本轮只改善自动驾驶 summary 的普通用户表达，不执行 Nav2、不准备路线、不发送任何运动命令。
- live 完整路线仍需要现场勾选安全确认后重跑，并在同窗口证明轮速 L/R 非零；本轮未触发执行。
