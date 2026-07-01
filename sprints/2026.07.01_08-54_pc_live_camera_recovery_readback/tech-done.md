# 2026.07.01 08:54 PC 当前卡点画面复测入口

## sprint_type

micro

## 实际改动

- 在 PC 普通首屏当前卡点区新增 `plain-live-camera-recovery-readback`，当画面未可见时直接展示相机恢复下一步。
- 新增 `plain-live-camera-recovery-refresh`，复用既有相机只读复测链路：相机首帧 probe、共享 MJPEG status、summary 刷新。
- 明确 DOM 合同：该入口不刷新雷达 scan proof、不刷新地图预览、不启动相机独占采集、不启动雷达 lifecycle、不启动建图 runtime、不执行 Nav2、不发送手控/键盘/自由移动、不提交 delivery、不 stop、不发送 motion。
- 复用既有 USB full-speed 判定：当诊断为 `uvc_full_speed_usb_not_exclusive` 或文案包含 USB 12M full-speed/高速 USB/带供电 Hub 时，当前卡点按钮显示“换USB后复测”。
- 更新 PC 工作站产品边界文档，记录当前卡点画面复测入口和 no-motion 边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，结果 `1 passed | 230 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "labels full-speed USB camera recovery as USB fix before recheck"`，结果 `1 passed | 230 skipped`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，生成 `dist/assets/index-81jqVXbE.js` 与既有 CSS；仅保留 Vite 大 chunk 提示。
- 通过：`cd pc-tools/workstation && npm test`，结果 `3 passed`、`417 passed`。
- 通过：`git diff --check`。
- 通过：重启 PC API 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`，PID `87687`。
- 通过：`curl -I http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`。
- 通过：构建产物 `dist/assets/index-81jqVXbE.js` 包含 `plain-live-camera-recovery-readback`、`plain-live-camera-recovery-refresh`、`画面复测` 和 `换USB后复测`。
- 通过：真实 no-motion `POST /api/robot-control/camera/first-frame/probe?force=true` 返回 `proxy_status=probe_failed`、`status=blocked`、`robot_control_executed=false`、`hard_dangerous_true_fields=[]`。
- 通过：随后 `GET /api/robot-control/camera/mjpeg/status` 返回 `exclusive_camera_claim=false`、`robot_control_executed=false`，仍未读到当前帧。
- 通过：随后 `GET /api/robot-control/summary` 返回 `camera_current_visible=false`、`live_wysiwyg_camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`live_wysiwyg_camera_source_diagnosis_not_exclusive=true`，同时 `radar_map_points_visible=true`。

## 剩余风险

- 当前改动是 PC 只读 UI/DOM 合同；真实画面仍需要现场把摄像头从 USB 12M full-speed 链路换到高速 USB 口/线或带供电 Hub 后再复测。
- 当前只读状态已经证明地图、路线和雷达贴图 WYSIWYG；完整 Nav2 闭环仍缺同窗口 wheel L/R 非零和 delivery success，需要现场安全确认后的运动窗口验证。
