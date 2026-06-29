# 2026.06.30 05:54 PC Map Observer Mode

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图新增 `观测模式` 按钮。
  - 进入观测模式时自动切到全屏地图，退出时恢复普通大地图。
  - 地图卡新增 `data-observer-mode` 与 `data-ros2-companion-style=rviz2-map-focus`，用于验收 PC 内置 RViz-like 只读观察模式。
- `pc-tools/workstation/src/styles.css`
  - 观测模式下收起地图卡下方普通操作行和说明，让地图 overlay 使用更多浏览器高度。
  - 移动端保留较低最小高度，避免小屏文字和按钮溢出。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖默认非观测、进入观测、退出观测和观测模式样式合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明 PC 观测模式与 ROS2/RViz2 工程配套边界。

## 验证结果

- `npm test -- test/App.test.ts -t "Robot Control V1 by default"`：通过。
- `npm test -- --run`：通过，2 files / 389 tests。
- `npm run build`：通过，生成 `dist/assets/index-ahBMtgcp.js` 与 `dist/assets/index-CtXHTNuY.css`；Vite 仅保留既有大 chunk warning。
- `git diff --check`：通过。
- 7001 smoke：通过。`HOST=0.0.0.0 PORT=7001 npm run api` 已重启，PID `70248` 监听 `TCP *:7001`；`curl -fsS http://127.0.0.1:7001/` 返回新 bundle `/assets/index-ahBMtgcp.js` 和 `/assets/index-CtXHTNuY.css`；dist bundle 可搜到 `data-observer-mode`、`rviz2-map-focus` 和 `plain-map-observer-toggle`。

## 剩余风险

- 本轮只改 PC Web 只读显示和 DOM 合同，没有启动 RViz2、ROS2 runtime、Nav2、自由移动、键盘手控或建图。
- 未做真实浏览器截图验收；观测模式尺寸通过 CSS 合同和组件测试覆盖。
