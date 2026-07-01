# PC 当前卡点扁平接口

sprint_type: micro

## 实际改动

- 新增 `GET /api/robot-control/live-summary`，返回同一次 summary 聚合里的 `live_closure_summary` 扁平 JSON，方便现场直接 `curl | jq` 查看当前卡点、路线/轮速/画面/雷达/自由移动/建图缺口。
- 抽出 `buildRobotControlSummaryForHttp`，让 `/api/robot-control/summary` 和 `/api/robot-control/live-summary` 共用同一份只读相机首帧 overlay、MJPEG relay 状态和 summary 聚合逻辑。
- 新增 `RobotControlLiveSummaryResponse` 合同类型和 catalog 集成测试，验证扁平接口同源于 summary、保持只读安全字段，不触发 Nav2/manual/free-roam/map start/delivery 等控制路径。
- 更新 PC 产品文档，明确 live-summary 是现场脚本只读入口，不替代任何发车确认。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`，结果 `1 passed | 179 skipped`。
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `7 passed`。
- 通过：`npm run lint`，结果 `eslint .` 无报错。
- 通过：`npm run build`，结果 `tsc` 与 `vite build` 通过；保留既有 chunk size warning。
- 通过：`npm test`，结果 `3 passed` 测试文件、`418 passed` 用例。
- 通过：`git diff --check`，无空白错误。
- 通过：本机 7001 实测，`lsof` 显示 `node` 监听 `*:7001`；`curl http://127.0.0.1:7001/api/robot-control/live-summary | jq ...` 返回 schema `trashbot.pc_tools_workstation.robot_control_live_summary.v1`，当前卡点 `needs_wheel_rerun`，并显示 `readback_only=true`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`submits_delivery=false`、`stops_motion=false`、`publishes_cmd_vel=false`。

## 剩余风险

- 该接口只改善现场读状态的可用性，不会自动完成真实轮速非零、delivery success、相机首帧或雷达贴图闭环；这些仍需要现场安全确认后的实际执行与只读验收。
