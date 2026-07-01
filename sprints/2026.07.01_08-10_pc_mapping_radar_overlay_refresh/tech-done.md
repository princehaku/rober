# 建图雷达贴图只读刷新

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在 `plain-mapping-unlock-summary` 判定雷达阻塞建图时显示 `plain-mapping-radar-overlay-refresh`。
  - 按钮复用 no-motion 雷达读回链路：刷新 radar scan proof，再读取 radar status 和 map preview。
  - 按钮只解决“雷达已开始但地图贴图 stale”的 WYSIWYG 卡点，不启动雷达 lifecycle、不启动建图、不启动自由移动、不执行 Nav2/manual/keyboard/delivery/stop。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖雷达阻塞建图时按钮出现、固定端点、点击后的只读请求，以及不触发 motion/control POST。
- `docs/product/pc_tools_workstation.md`
  - 同步建图卡点旁边的雷达贴图刷新合同。

## 验证结果

- 通过：现场 no-motion `POST /api/robot-control/radar/scan-proof/refresh` 返回 `latest_scan_proof_fresh=true`、`scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`、`robot_control_executed=false`。
- 通过：随后只读 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=4`、`radar_overlay_refresh_required=false`。
- 通过：随后只读 summary 返回 `mapping_start_missing_reasons=[camera_first_frame]`、`mapping_lidar_blocks_start=false`、`mapping_camera_blocks_start=true`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "splits free movement"`，1 file passed，1 test passed，230 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，PID `13231`。
- 通过：只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `robot_api_connection_status=readable`、`radar_map_points_visible=true`、`mapping_start_missing_reasons=[camera_first_frame]`、`mapping_lidar_blocks_start=false`、`mapping_camera_blocks_start=true`、`camera_diagnosis=uvc_full_speed_usb_not_exclusive`。
- 通过：构建产物 `pc-tools/workstation/dist/assets/index-snTLw3j3.js` 包含 `plain-mapping-radar-overlay-refresh` / “刷新雷达贴图”。

## 剩余风险

- 本轮只增加 no-motion 雷达贴图刷新入口，不执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 真实建图启动仍缺相机首帧；相机诊断仍指向 USB 12M full-speed，需要换高速 USB 口/线或带供电 Hub 后复测。
- 完整 Nav2 行程仍待现场安全确认后重跑，并复验同窗口 wheel L/R 非零和 delivery success。
