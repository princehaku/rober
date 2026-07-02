# Motion pack safety aliases

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 为完整 Nav2 行程、PC 键盘连续手控和自由自助移动三个当前控制包补齐统一命名 alias：
  - `current_trip_execution_pack_safety_confirm_required`
  - `current_keyboard_control_pack_safety_confirm_required`
  - `current_free_move_control_pack_safety_confirm_required`
- 普通首屏三个包节点同步暴露 `data-safety-confirm-required`，与既有 `data-requires-safety-confirm` 同源，便于现场脚本用统一字段确认发车前预检只剩安全确认。
- 文档同步记录该 alias 只读边界，并把 PC 地图大屏口径对齐为当前 `3200%` 默认缩放、`6400%` 最大缩放；ROS2 配套仍是工程观察用 RViz2 / Foxglove，不替代普通用户 `/map` 大屏。

## 验证结果

- `npm test -- test/robotControlSummary.test.ts`
  - 通过，`1 passed`，`10 passed`。
- `npm test -- test/App.test.ts`
  - 通过，`1 passed`，`237 passed`。
- `npm run build`
  - 通过，输出 `dist/index.html`、`dist/assets/index-BWCYxP2w.css`、`dist/assets/index-Bpb14Xof.js`。
  - Vite 仍提示单 chunk 大于 500 kB，这是既有体积警告，不影响本轮改动。
- `git diff --check`
  - 通过，无空白错误。
- 重启 PC workstation 到 `0.0.0.0:7001` 后只读验证：
  - `GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
  - `GET /api/robot-control/summary` 返回三个 `*_safety_confirm_required=true`，且地图字段为 `map_display_default_zoom_percent=3200%`、`map_display_max_zoom_percent=6400%`、`map_display_primary_url=/map`。
  - `curl -I http://127.0.0.1:7001/map` 返回 HTTP `200 OK`。

## 剩余风险

- 本轮没有发送任何运动命令，未执行 Nav2 路线、键盘按住移动、自由移动或 delivery，因此 `wheel raw L/R 非零`、`delivery success` 和自由移动真实运行证据仍需现场安全确认后 HIL 验证。
- 摄像头首帧仍受当前 USB full-speed / UVC 取帧问题影响，建图启动仍缺 `camera_first_frame`。
- 工作区仍保留既有未纳入本轮的 artifact dirty 文件，本轮不处理也不提交。
