# 建图解锁摘要

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏 `plain-mapping-unlock-plan` 顶部新增 `plain-mapping-unlock-summary`。
  - 摘要把画面首帧、雷达刷新、建图启动 ready、缺口和下一步合并成一句普通用户能扫读的结论。
  - DOM 明确暴露 `data-camera-blocks-mapping-start`、`data-radar-blocks-mapping-start`、`data-camera-ready-for-mapping`、`data-radar-ready-for-mapping` 和固定只读复测端点。
  - 保持 no-motion 边界：不启动建图 runtime、不启动自由移动、不执行 Nav2/manual/keyboard/delivery/stop。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖“雷达已满足、只差画面首帧”的建图解锁摘要，以及 no-motion DOM 属性。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 工作站建图解锁摘要合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1"`，1 file passed，1 test passed，230 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，PID `2562`。
- 通过：只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `robot_api_connection_status=readable`、`objective_status=in_progress`、`objective_done=1/4`、`mapping_start_ready=false`、`mapping_start_missing_reasons=[camera_first_frame]`、`mapping_camera_blocks_start=true`、`mapping_lidar_blocks_start=false`、`camera_diagnosis=uvc_full_speed_usb_not_exclusive`。
- 通过：构建产物 `pc-tools/workstation/dist/assets/index-Ct30LC0J.js` 包含 `plain-mapping-unlock-summary` / “建图解锁”。

## 剩余风险

- 本轮只改 PC 普通首屏建图解锁提示，不执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 当前真实现场仍缺相机首帧，建图启动必须等 USB full-speed 问题修复并复测首帧后再进行。
- 完整 Nav2 行程仍待现场安全确认后重跑，并复验同窗口 wheel L/R 非零和 delivery success。
