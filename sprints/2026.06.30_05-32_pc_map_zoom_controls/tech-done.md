# 2026.06.30 05:32 PC Map Zoom Controls

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图新增内置缩放状态与 `+`、`-`、`适配` 控件，默认 `125%`。
  - 地图卡、缩放控件和 overlay frame 暴露 `data-map-zoom-scale`、`data-map-zoom-percent`、`data-map-zoom-affects=image-route-robot-radar`，用于证明缩放会同时作用到底图、路线、小车位置和雷达点。
- `pc-tools/workstation/src/styles.css`
  - 地图 layer 改为可滚动视口，overlay frame 用同一个 `--plain-map-zoom` 放大，避免只放大底图或只放大 marker。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展普通首屏测试，覆盖默认 125%、放大到 150%、适配回 100%、缩放 DOM 合同和 CSS 缩放实现。
- `pc-tools/README.md`
  - 记录普通首屏地图内置缩放与 RViz2 工程调试边界。
- `docs/product/pc_tools_workstation.md`
  - 同步普通用户地图缩放产品口径。

## 验证结果

- `npm test -- test/App.test.ts -t "Robot Control V1 by default"`：通过，1 passed / 218 skipped。
- `npm test -- --run`：通过，2 个 test files、389 个 tests 全部通过。
- `npm run build`：通过，Vite 仍有既有 bundle size warning。
- `git diff --check`：通过，无 whitespace 错误。
- PC Node `0.0.0.0:7001`：已重启，`lsof` 显示 `node` PID `24631` 监听 `TCP *:7001`。
- `curl -fsS http://127.0.0.1:7001/`：通过，返回当前构建入口 `/assets/index-LkAFWDRt.js` 和 `/assets/index-Qsyb8IAr.css`。
- `curl -fsS http://127.0.0.1:7001/assets/index-LkAFWDRt.js | rg -q "data-map-zoom-affects"`：通过，JS bundle 包含缩放 DOM 合同。
- `curl -fsS http://127.0.0.1:7001/assets/index-Qsyb8IAr.css | rg -q "plain-map-zoom-controls"`：通过，CSS bundle 包含缩放控件样式。

## 剩余风险

- 本轮只做 PC Web 侧只读显示放大，没有启动 RViz2、ROS2 runtime、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 缩放控件的真实滚动手感仍需要现场浏览器人工体验；自动测试只验证 DOM 合同、状态切换和 CSS 关键规则。
