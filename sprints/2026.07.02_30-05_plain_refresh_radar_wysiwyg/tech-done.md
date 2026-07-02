# Plain refresh radar WYSIWYG

## sprint_type

micro

## 实际改动

- PC 普通首屏 `连接/刷新` 从“刷新 summary + map preview + radar status + camera status”升级为“刷新 summary 后，先执行 no-motion radar scan proof，再读 radar status + map preview + camera status”。
- `robot-api-refresh` 按钮新增 DOM 合同，明确会刷新 radar scan proof、map preview、radar status 和 camera MJPEG status，同时暴露完整 no-motion 边界。
- `App.test.ts` 补充普通刷新会调用 `/api/robot-control/radar/scan-proof/refresh` 的断言，并确认它不会触发 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md` 同步记录普通首屏刷新也必须保障雷达贴图 WYSIWYG。

## 验证结果

- `npm test -- --run App.test.ts robotControlSummary.test.ts`
  - 结果：通过，`2 passed`，`247 passed`。
- `npm run build`
  - 结果：通过，产物包含 `dist/index.html`、`dist/assets/index-CV6yLOmZ.css`、`dist/assets/index-zKkgoz9w.js`。
  - 备注：Vite 仍提示单 chunk 大于 500 kB，这是既有体积警告，不影响本轮功能验证。
- `npm run lint`
  - 结果：通过。
- `git diff --check`
  - 结果：通过，无空白错误。
- `GET http://127.0.0.1:7001/map`
  - 结果：HTTP `200 OK`。
- `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` live 读回：
  - `current_radar_map_wysiwyg_pack_status=loaded`
  - `current_radar_map_wysiwyg_pack_current_point_count=154`
  - `current_radar_map_wysiwyg_pack_needs_refresh=false`
  - `current_radar_map_wysiwyg_pack_loaded=true`
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `mapping_lidar_fresh_readback_ready=true`
  - `mapping_lidar_fresh_gate_status=ready`
  - `current_mapping_action_missing_evidence=["camera_first_frame"]`
  - `current_mapping_action_radar_ready=true`
  - `current_camera_wysiwyg_pack_status=needs_first_frame`
  - `current_camera_wysiwyg_pack_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `current_camera_wysiwyg_pack_usb_speed=12M`

## 剩余风险

- 本轮不发送运动命令，只推进 PC 首页只读 WYSIWYG 刷新链路。
- 相机首帧仍受现场 USB full-speed/硬件输入影响；完整 Nav2 行程、wheel raw L/R 非零、delivery success 和自由移动启动读回仍需现场安全确认后继续验收。
