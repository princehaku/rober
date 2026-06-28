# PC 建图雷达下一步提示补齐

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 中补齐建图验收文案：当地图雷达 overlay 已明确为 `not_current`，且后端给出 `start_radar_then_refresh_map_preview` 时，普通用户的建图 readiness 卡直接提示“建图下一步：先启动雷达，再刷新地图画面”。
- 在 `pc-tools/workstation/test/App.test.ts` 的旧雷达点不贴图场景中新增断言，确保建图卡承接同一个下一步提示，同时继续确认不会自动调用雷达启动、底盘手控、Nav2 执行或 `cmd_vel`。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "honors not-current map radar overlay summary"` 通过：1 passed, 366 skipped。
- `npm --prefix pc-tools/workstation test` 通过：2 files passed, 367 tests passed。
- `npm --prefix pc-tools/workstation run build` 通过；仅保留 Vite chunk size 既有警告。
- 只读查询 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 通过，现场仍为 `console_status=loaded_fail_closed_summary`、`map.radar_overlay_status=not_current`、`map.radar_overlay_next_action=start_radar_then_refresh_map_preview`、`free_roam.start_ready=true`。

## 剩余风险

- 本轮没有现场安全确认，因此没有触发发车、键盘手控、Nav2 路线执行、雷达启动或相机占用类动作；真实运动闭环仍需 CEO 现场确认后再执行。
- 摄像头当前只读诊断仍指向 `source_first_frame_failed` / `uvc_no_frame_not_exclusive`，需要继续做 USB 输入、供电或 known-good UVC 复测。
- 雷达当前只读诊断仍为 `not_current`，本轮只把下一步显式前置到建图卡，没有自动启动雷达。
