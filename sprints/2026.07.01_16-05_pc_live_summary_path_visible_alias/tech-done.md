# PC live-summary 路线可见 alias 修复

sprint_type: micro

## 实际改动

- `live_closure_summary` 和 `/api/robot-control/live-summary` 新增 `path_current_visible`，直接暴露当前地图上的图上路线可见性，避免现场 `curl | jq` 读到 `null`。
- PC 普通首屏 `plain-live-closure-summary` 增加 `data-path-current-visible`，让 DOM smoke 可以同时确认地图和路线所见即所得。
- 更新产品文档和测试，明确该字段只读，不触发 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "minimal precheck fields for same-window wheel rerun"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "keeps live closure wheel rerun as a focus-only Nav2 action"`：通过，1 passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单包 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- `cd pc-tools/workstation && npm test`：通过，3 files / 418 tests。
- `git diff --check`：通过。
- 运行态只读确认：PC API 已重启到 `0.0.0.0:7001`，`GET /api/robot-control/live-summary` 返回 `nav2_route_ready=true`、`map_current_visible=true`、`path_current_visible=true`、`live_wysiwyg_map_visible=true`，地图默认缩放仍为 `600%`。

## 剩余风险

- 本轮只修复 live-summary/DOM 的路线可见性 alias；真实雷达贴图仍需要只读刷新雷达扫描后再刷新地图，摄像头首帧仍受 USB full-speed 硬件链路影响。
