# PC Radar Map Marker Proof Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainRadarStartMapProofSummary`，把雷达启动/重启后的地图刷新、当前雷达点贴图、旧点抑制和固定 map preview endpoint 合成普通首屏验收条。
  - 雷达卡新增 `data-testid="plain-radar-start-map-proof"`，结构化暴露 `data-radar-start-map-refresh-pending/failed/complete`、`data-radar-map-points-visible`、`data-radar-map-point-count`、`data-radar-old-points-suppressed` 等字段。
- `pc-tools/workstation/src/styles.css`
  - 新增 `.plain-radar-start-map-proof` 状态样式，用于区分待贴图、刷新中、刷新失败、旧点抑制和已贴图。
- `pc-tools/workstation/test/App.test.ts`
  - 补默认首屏、旧点抑制、雷达启动后刷新中、地图刷新完成已贴图的 DOM 和文案断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏雷达贴图验收条和只读安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "radar"`：通过，33 个雷达相关测试通过。
- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，默认首屏测试通过。
- `npm test -- --run`：通过，2 个测试文件、391 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-CY1u8ErQ.js` 与 `dist/assets/index-lzj5zyBl.css`。
- `git diff --check`：通过。
- 7001 重启：新监听进程为 `node` PID `71142`，地址 `TCP *:7001`。
- live bundle 检查：`http://127.0.0.1:7001/` 已引用 `index-CY1u8ErQ.js` 和 `index-lzj5zyBl.css`；JS 资源命中 `plain-radar-start-map-proof`、`雷达贴图验收`、`启动/重启后的地图刷新已完成`、`旧雷达点不算当前点`、`data-radar-start-map-refresh-complete`、`data-radar-old-points-suppressed`，CSS 资源命中 `.plain-radar-start-map-proof`。

## 剩余风险

- 本轮只补 PC Web 显示和只读 DOM 合同，不自动启动雷达、不刷新地图、不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- 未做真车 HIL；真实雷达贴图仍需现场启动雷达并观察地图刷新后的 marker。
