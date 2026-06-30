# PC Mapping Unlock WYSIWYG Refresh Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `refreshPlainMappingUnlockEvidence()`，让“传感器就绪后建图”里的 `plain-mapping-unlock-refresh` 复用当前所见 no-motion 证据刷新链路。
  - `plain-mapping-unlock-refresh` 点击后会触发相机首帧 probe、雷达 scan proof、地图 preview、radar status 和 camera MJPEG status 刷新。
  - 按钮新增固定 endpoint 与 no-motion DOM 合同，明确不启动建图、不启动自由移动、不发送运动命令。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定 `plain-mapping-unlock-refresh` 会 POST `/api/robot-control/radar/scan-proof/refresh` 与 `/api/robot-control/camera/first-frame/probe`。
  - 锁定该按钮不会调用 radar start、map start、free-roam start、Nav2 execute、manual 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录建图条件刷新从 summary-only 改为真实 WYSIWYG 证据刷新。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标测试通过，222 个测试按筛选跳过。
- `npm test -- --run`：通过，2 个测试文件、397 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-2xWdwysU.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `15930`，新监听进程为 `node` PID `31307`，地址 `TCP *:7001`。
- 7001 只读 bundle smoke：`http://127.0.0.1:7001/` 已引用 `index-2xWdwysU.js` / `index-BBcFFzNr.css`；JS 资源命中 `plain-mapping-unlock-refresh`、`data-refreshes-camera-first-frame-probe`、`data-refreshes-radar-scan-proof`、`camera/first-frame/probe` 和 `radar/scan-proof/refresh`。
- 7001 live summary 只读 GET：`free_roam_motion_start_ready=true`，`free_roam_mapping_start_ready=false`，建图缺口为 `camera_first_frame`、`lidar_fresh`，`live_status=needs_wheel_rerun`，`sends_motion_when_clicked=false`。

## 剩余风险

- 本轮没有触发真实 `plain-mapping-unlock-refresh` POST，也没有启动建图、自由移动或任何运动命令；live smoke 仅做首页、静态 bundle 与 summary GET。
- 真实建图仍取决于现场相机首帧和雷达新鲜扫描；当前 live summary 仍显示缺 `camera_first_frame` 与 `lidar_fresh`。
