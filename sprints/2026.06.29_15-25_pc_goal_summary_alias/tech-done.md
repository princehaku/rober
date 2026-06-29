# PC 目标总览兼容字段

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlSummaryResponse` 新增顶层只读 alias `goal_summary?: RobotControlGoalChecklistSummary`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：正常 summary 和 fail-closed summary 都返回同一份 `goalSummary` 对象到 `goal_checklist_summary` 与 `goal_summary`，避免字段漂移。
- `pc-tools/workstation/test/catalog.test.ts`：补充正常 summary、missing baseUrl 和 unsafe URL 三类回归，证明 alias 与原字段完全一致。
- `docs/product/pc_tools_workstation.md`：同步 `goal_summary` 兼容合同和安全边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "proxies Robot API readback endpoints"`，正常 summary 合同回归通过。
- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "rejects unsafe URLs"`，fail-closed summary 合同回归通过。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、382 个用例通过。
- 通过：`npm --prefix pc-tools/workstation run build`，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过；Vite 仍保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启本机 PC API 到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`，启动日志为 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读 `GET /api/health` 返回 `schema=trashbot.pc_tools_workstation.health.v1`、`mode=pc_only_readonly_workstation`、`version=0.2.0`。
- 通过：只读 `GET /api/robot-control/summary` 返回 `robot_api_connection.status=readable`，`goal_summary` 存在且 JSON 等于 `goal_checklist_summary`；live `ready_action_items=[free_move,keyboard_continuous_control,nav2_route_execution]`，`blocked_action_items=[camera_wysiwyg,radar_map_points_wysiwyg,mapping_start]`。

## 剩余风险

- 本轮只补只读 API 易用性，不启动雷达、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实目标仍未完成：摄像头 UVC 无首帧、雷达未启动、Nav2 需要 ROS 重跑同窗口 wheel L/R 复验、建图需要相机和雷达 ready 后现场验证。
