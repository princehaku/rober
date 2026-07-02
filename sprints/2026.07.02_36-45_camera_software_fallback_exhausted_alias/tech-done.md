# Camera Software Fallback Exhausted Alias

## sprint_type

micro

## 实际改动

- 在 PC workstation summary 中新增 `current_camera_wysiwyg_pack_software_fallback_exhausted`、`current_camera_wysiwyg_pack_requires_physical_usb_fix`、`current_camera_wysiwyg_pack_physical_fix_label`。
- 在普通用户 PC 首屏 `plain-current-camera-wysiwyg-pack` DOM 同步输出 `data-software-fallback-exhausted`、`data-requires-physical-usb-fix`、`data-physical-fix-label`，用于现场判断相机低带宽软件降级是否已经耗尽。
- 更新 `docs/product/pc_tools_workstation.md`，说明 160x120 fallback 后仍无首帧时的 USB 物理处理边界：只读、不发车、不阻塞自由移动。
- 更新 summary 与 App 单测，固定 USB 12M full-speed + 160x120 fallback 仍超时的硬件处理结论。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，10 tests passed。
- 通过：`npm test -- test/App.test.ts`，237 tests passed。
- 通过：`npm run build`，TypeScript 与 Vite build 均完成；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001`，新 PID `47983`。
- 通过：只读调用 `/api/robot-control/camera/first-frame/probe` 后读取 `/api/robot-control/summary`，现场返回 `current_camera_wysiwyg_pack_software_fallback_exhausted=true`、`current_camera_wysiwyg_pack_requires_physical_usb_fix=true`、`current_camera_wysiwyg_pack_physical_fix_label=换高速USB后复测`、`current_camera_wysiwyg_pack_low_bandwidth_fallback_min_size=160x120`、`current_camera_wysiwyg_pack_usb_speed=12M`、`current_radar_map_wysiwyg_pack_status=loaded`、`current_goal_free_move_allowed_while_mapping_blocked=true`。probe 回包确认 `sends_motion_when_clicked=false`、`starts_nav2=false`、`starts_manual=false`、`starts_free_roam=false`、`starts_map_runtime=false`。

## 剩余风险

- 当前相机仍需要现场把 USB 摄像头换到高速 USB 口/线或带供电 Hub 后复测；本轮只补齐 PC 端可见的判定字段，不发送运动命令。
