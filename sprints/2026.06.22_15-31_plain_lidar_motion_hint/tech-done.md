# Plain LiDAR Motion Hint

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 普通首屏“轮速记录”新增“雷达移动记录”缺口提示，解释 LiDAR motion delta 为什么仍会阻止键盘手控解锁。
- 如果只读 summary 仍缺雷达移动记录，提示“试动时需要雷达看到前后变化”；如果 first-jog 返回 `physical_motion_lidar_delta_not_proven`，提示检查雷达运行和现场空间后重试。
- 该提示不调用雷达 start/stop、manual、first-jog、Nav2 或 `/cmd_vel`。
- 补测试确认普通首屏显示中文缺口提示，且不暴露 `physical_motion_lidar_delta_proven` 字段名。
- 更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test`，2 个 test files、118 个 tests 全部通过。
- 通过：`npm run lint`。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改善 PC 首屏解释，不完成真实 LiDAR motion delta。
- 真实键盘连续手控仍需要 wheel raw L/R 非零和 LiDAR motion delta 都由现场试动证据满足。
