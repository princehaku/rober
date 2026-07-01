# 2026.07.02 15:00 Mapping Readback Aliases

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlSummaryResponse` 新增 `mapping_readback_endpoints` 和 `mapping_required_success_markers`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 顶层从 `buildLiveMotionRunbook` 的 `start_mapping` 条目同源输出建图验收读回端点和成功 marker。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-field-acceptance-packet` DOM 暴露 `data-mapping-readback-endpoints` 和 `data-mapping-required-success-markers`，方便现场 DOM smoke 不解析嵌套 runbook。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：补 summary 和 DOM 回归断言。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明建图读回 alias 只读，不启动建图 runtime 或任何运动控制。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 files / 427 tests passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 仍有既有 chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`。
- 真实 summary smoke：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `mapping_readback_endpoints=[/api/robot-control/free-roam/autonomy/latest,/api/robot-control/map/preview,/api/robot-control/summary]`、`mapping_required_success_markers=[camera_first_frame]`，并确认 `map_display_primary_url=/map`、`map_display_default_zoom_percent=1600%`、ROS2 配套白话字段非空。
- `/map` 静态入口 HTTP 200，返回当前构建产物。

## 剩余风险

- 本轮只补建图读回 alias 和 PC/summary 可见性，不发运动命令，也不启动建图 runtime。
- 运动目标仍需要现场安全确认后的完整 Nav2 wheel L/R 非零、delivery success、PC 键盘连续手控和自由移动验收。
- 当前 WYSIWYG / mapping 仍缺相机首帧；雷达贴图在本次真实 summary 中已显示 `radar_overlay_wysiwyg_complete=true`。
- 仓库没有 Playwright 依赖，本轮未新增浏览器截图依赖；视觉收口依据为 DOM 合同、构建产物 `/map` HTTP smoke 和真实 summary 读回。
