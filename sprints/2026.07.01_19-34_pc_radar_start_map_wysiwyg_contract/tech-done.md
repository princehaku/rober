# PC radar start map WYSIWYG contract

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 在 live closure summary 和 summary 顶层 alias 中新增雷达启动/重启后的地图贴图 WYSIWYG 合同字段。
  - 合同明确雷达 start/restart 不是底盘运动，但必须串联 summary、scan proof、radar status 和 map preview。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 输出 `radar_start_map_wysiwyg_required=true`、固定刷新顺序和 no-motion 边界。
  - 顶层 alias 与 `live_closure_summary` 同源，方便现场脚本一条 summary 验收。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-radar-panel`、`plain-radar-refresh`、`plain-radar-start`、`plain-radar-restart` 补齐雷达贴图 WYSIWYG 和 no-motion DOM 合同。
  - 启动/重启雷达按钮明确只启动/重启雷达 lifecycle，不启动 Nav2、manual、keyboard、free-roam、建图 runtime、delivery 或底盘 stop。
- `pc-tools/workstation/test/App.test.ts`
  - 增加首屏雷达卡、启动按钮、重启按钮的 WYSIWYG 序列和 no-motion 边界断言。
- `docs/product/pc_tools_workstation.md`
  - 同步雷达启动/重启后的地图标记 WYSIWYG 合同。

## 验证结果

- 现场 no-motion 雷达贴图刷新：
  - `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=refresh_forwarded`、`robot_control_executed=false`。
  - 随后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=72`、`radar_overlay_source_point_count=104`、`radar_overlay_needs_refresh=false`、`radar_overlay_blocks_wysiwyg=false`、`radar_overlay_refresh_sends_motion=false`、`radar_overlay_refresh_starts_radar_lifecycle=false`。
  - 随后 summary 返回 `live_wysiwyg_missing_surface_ids=["camera"]`，说明雷达贴图缺口已通过 no-motion 刷新收敛，当前只剩相机首帧缺口。
- `npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 231 passed (231)`。
- `npm --prefix pc-tools/workstation run lint`
  - 通过：`eslint .` 无错误输出。
- `npm --prefix pc-tools/workstation run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
  - Vite 仍提示单 bundle 超过 500 kB，这是既有体积警告，不影响本轮合同。
- `npm --prefix pc-tools/workstation test -- --run`
  - 通过：`Test Files 3 passed (3)`，`Tests 421 passed (421)`。
- PC 7001 smoke：
  - 已重启 PC 工作站到 `0.0.0.0:7001`；最终复核监听进程为 `node` PID `30096`。
  - `GET http://127.0.0.1:7001/` 返回 `200`。
  - `GET http://127.0.0.1:7001/map` 返回 `200`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `radar_start_map_wysiwyg_required=true`，刷新顺序为 `/api/robot-control/radar/start,/api/robot-control/summary,/api/robot-control/radar/scan-proof/refresh,/api/robot-control/radar/status,/api/robot-control/map/preview`，且 `radar_start_sends_motion=false`、`radar_start_starts_nav2=false`、`radar_start_starts_manual=false`、`radar_start_starts_keyboard=false`、`radar_start_starts_free_roam=false`、`radar_start_starts_map_runtime=false`、`radar_start_submits_delivery=false`、`radar_start_stops_motion=false`。
  - 当前 live summary 显示 `radar_overlay_status=loaded`、`live_wysiwyg_missing_surface_ids=["camera"]`。
  - 当前 bundle `/assets/index-IqRcQERr.js` 包含 `radar-start-map-wysiwyg`、`data-radar-start-sends-motion`、`data-stops-radar-lifecycle` 和 `plain-radar-start`。

## 剩余风险

- 本轮没有执行任何真实底盘运动，也没有真实点击雷达 start/restart；雷达贴图恢复只覆盖 no-motion scan proof + map preview 刷新。
- 真实建图仍未解锁：当前 summary 只剩 `camera_first_frame` 缺口，摄像头显示需要继续处理 USB full-speed/首帧问题。
