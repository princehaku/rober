# 地图雷达状态 WYSIWYG 接入

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `radarStatusResult`，把显式地图画面刷新时读取到的 `/api/robot-control/radar/status` 合并为有效雷达 readback。
  - 地图雷达 marker、雷达卡片和键盘/扫图相关提示优先使用最新 radar status；summary 仍作为兼容兜底。
  - 普通地图“刷新地图画面”和扫图地图刷新会并发读取地图预览与雷达状态；初始化/内部自动预览不覆盖 summary 口径。
  - radar status 读取失败时保留地图预览，并用失败 fallback 影响 marker 口径，不吞掉地图画面。
- `pc-tools/workstation/src/server/index.ts`
  - `radar_key_values` 继续补齐 `continuous_window_observed`、`lifecycle_running`、`lifecycle_state`、`lifecycle_status`，让前端能用只读 radar status 完整判断运行/过期状态。
- `pc-tools/workstation/test/App.test.ts`
  - 增加回归测试：summary 仍显示雷达 fresh，但显式刷新地图画面时 radar status 返回 stale，地图 marker 必须降级为“雷达待刷新”。
  - 更新测试桩支持 `/api/robot-control/radar/status`。

## 验证结果

- `npm test`：通过，2 个 test files，220 个 tests passed。
- `npm run build`：通过；Vite 仍提示单 chunk 大于 500 kB 的既有 warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 7001 真机只读 smoke：通过。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node ... TCP *:7001 (LISTEN)`。
  - 并发读取 `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 与 `GET /api/robot-control/radar/status?baseUrl=http://192.168.1.11:8787` 均返回 HTTP 200。
  - 地图返回 `proxy_status=preview_forwarded`、`width=223`、`height=116`、`has_free_cells=true`。
  - 雷达返回 `proxy_status=status_loaded`、`lifecycle_running=true`、`continuous_scan_status=latest_proof_stale_while_lifecycle_running`、`latest_scan_proof_fresh=false`、`robot_control_executed=false`。
  - summary 同步显示 `keyboard_control_mode=bounded_repeating_manual_pulse`，lidar stale 口径与 radar status 一致。

## 剩余风险

- 真机当前雷达 lifecycle 在跑，但 latest proof stale；前端已通过测试固定为“刷新地图画面后 marker 降级为雷达待刷新”，仍需要下一轮继续把 stale 后的一键刷新/自动恢复体验做顺。
