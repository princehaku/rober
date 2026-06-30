# PC 地图雷达贴图 WYSIWYG 验收

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图卡新增 `plain-map-radar-wysiwyg-proof`。
  - 该短行只认当前地图点层实际画出的雷达点：`已贴图`、`局部点`、`只有点数`、`旧点已抑制`、`未贴图` 分开表达，避免把旧点、局部点或只有点数误当作地图标记。
  - DOM 同步暴露当前地图点数、来源点数、frame、source、overlay status、局部点数、旧点抑制数、count-only 点数，以及固定只读 map preview / radar refresh endpoint。
  - 明确 `data-sends-motion-when-clicked=false`、`data-starts-radar=false`、`data-starts-map-runtime=false`、`data-starts-nav2=false`、`data-starts-manual=false`。
- `pc-tools/workstation/src/styles.css`
  - 新增地图雷达贴图验收块的状态样式，保持普通 PC 界面直读。
- `pc-tools/workstation/test/App.test.ts`
  - 默认首屏验证未贴图时不冒充点层。
  - 雷达 start mock 后验证地图预览返回点数组时该短行进入 `已贴图`，可见文案不泄露 `map_preview` / `overlay` / `raw`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录地图雷达 WYSIWYG 验收合同。

## 验证结果

- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，1 passed。
- `npm test -- --run test/App.test.ts -t "auto-refreshes radar proof after plain radar start reports ok"`：通过，1 passed。
- `npm test -- --run test/App.test.ts`：通过，230 passed。
- `npm run lint`：通过。
- `npm run build`：通过，包含 `tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json`；Vite 仍提示既有 bundle 超 500 kB。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`，PID `20989`。
- 只读 summary 读回：
  - `schema=trashbot.pc_tools_workstation.robot_control_summary.v1`
  - `console_status=loaded_fail_closed_summary`
  - `source_base_url=http://192.168.1.11:8787`
  - `camera_status=source_first_frame_failed`
  - `camera_source_readiness=first_frame_failed`
  - `map_status=not_proven`
  - `radar_overlay_status=not_current`
  - `radar_overlay_point_count=0`
  - `radar_overlay_source_point_count=28`
  - `lidar_status=latest_proof_stale_while_lifecycle_running`
  - `delivery_success=false`
  - `safe_to_control=false`

## 剩余风险

- 本轮没有发送真实雷达 start、Nav2、manual、keyboard、free-roam、mapping、delivery 或 stop 控制请求；雷达贴图真实闭环仍需现场安全口径下刷新雷达读数和地图画面。
- live 只读 summary 显示当前地图雷达 overlay 仍是 `not_current`，当前地图点 0 个、旧来源点 28 个；新 UI 会正确表达“旧点已抑制/未贴图”，但还没有把真实当前雷达点贴到地图。
- 摄像头仍是 `source_first_frame_failed`，画面 WYSIWYG 还未完成真实首帧闭环。
- Vite bundle size warning 是既有体积提示，本轮未处理代码拆包。
