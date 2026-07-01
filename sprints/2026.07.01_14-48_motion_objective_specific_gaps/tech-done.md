# 运动目标顶层具体缺口

sprint_type: micro

## 实际改动

- `objective_audit_summary_plain` 的运动目标从大类 `行程/键盘/自由移动` 改为按当前读回列出具体证据缺口。
- 当前现场口径应直接显示：图上行程还差同窗口轮速 L/R 非零和送达确认、键盘还差按住读到轮速 L/R 非零和松开后停稳、自由移动还差启动读回。
- 产品文档同步要求：该摘要只读，不自动执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "mapping sensor|live closure"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 构建成功；保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，420 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读验证 `GET /api/robot-control/live-summary`：`objective_audit_summary_plain` 返回 `图上行程还差同窗口轮速 L/R 非零、送达确认；键盘还差按住读到轮速 L/R 非零、松开后停稳；自由移动还差启动读回`，并保持 `nav2_route_ready=true`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero_proven=false`、`delivery_success=false`、`keyboard_continuous_motion_verified=false`、`free_roam_motion_ready=false`、`radar_map_points_visible=true`、`map_current_visible=true`、`path_current_visible=true`。

## 剩余风险

- 本轮只改只读摘要，没有执行任何运动命令。
- 真实轮速 L/R 非零、完整 Nav2 行程、delivery success、键盘连续手控和自由移动运行读回仍需要显式安全确认后的现场运动验收。
