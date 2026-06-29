# PC 自由移动低速 fallback 就绪口径

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中拆开自由移动两层 readiness：
  - `free_roam_autonomy_start_ready` 继续表示上车自由移动状态机是否已加载且可直接启动；
  - `free_roam_motion_start_ready` 表示普通用户是否可以先在现场安全确认后低速移动，允许走 PC 键盘/低速手控 fallback，不再因为相机首帧或雷达新鲜缺失而显示为整车不能动。
- 在 `readback_summary.free_roam` 中同步返回 `motion_start_ready=true` 的 fallback 事实，同时保留 `runtime_status=not_loaded`，避免把未加载 runtime 伪装成已 ready。
- 在 `pc-tools/workstation/test/catalog.test.ts` 与 `pc-tools/workstation/test/App.test.ts` 中更新断言：
  - 自由移动从 blocked/not_ready 进入待安全确认或现场可收口分组；
  - 建图启动仍然因为画面首帧、雷达新鲜缺口保持未就绪；
  - 目标 checklist 的运动入口优先指向自由移动安全确认，而不是隐藏在键盘工程入口里。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`，记录该只读 summary/UI 口径变化。

## 验证结果

- 已通过定向 server 验证：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked|keeps robot connection readable when optional radar latest endpoints are not installed"`，结果 `2 passed | 159 skipped`。
- 已通过首屏定向验证：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`，结果 `1 passed | 214 skipped`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `2 files / 376 tests passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，监听 Node PID 为 `8292`。
- 已通过 7001 只读 summary live 验证：
  - `safe_command_boundary.free_roam_autonomy_start_ready=false`，上车自由移动 runtime 未伪装成可启动；
  - `safe_command_boundary.free_roam_motion_start_ready=true`，PC 低速运动可先处理；
  - `safe_command_boundary.free_roam_mapping_start_ready=false`，建图启动仍缺 `camera_first_frame`、`lidar_fresh`；
  - `readback_summary.free_roam.runtime_status=not_loaded`，`motion_start_ready=true`；
  - camera live 仍为 `has_recent_frame=false`、共享预览非独占 `shared_preview_exclusive_camera_claim=false`；
  - radar live 仍未读到 fresh scan。

## 剩余风险

- 本轮只改只读 summary 和 PC 首屏展示，不调用 Nav2 execute、不启动 free-roam、不发送 keyboard/manual、delivery、stop 或 `/cmd_vel`。
- 真实运动仍需要现场勾选安全确认并由用户显式点击对应按钮；本轮不会替代真实 HIL 运动验证。
- 摄像头首帧和雷达 fresh scan 仍未满足，因此建图启动仍未 ready；这是正确保留的传感器验收缺口。
