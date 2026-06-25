# 2026-06-26 09:45 PC 扫图短轨迹 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图新增 `plain-map-free-roam-trail` SVG overlay。
  - 扫地式建图按住方向键/WASD 时显示 `扫图中` 短轨迹；松开或停止收口后保留 `已停止` 短轨迹。
  - 有 map-frame 位姿时轨迹贴近机器人位置；缺位姿时只显示占位轨迹，并在 aria 中声明不代表坐标或里程计轨迹。
- `pc-tools/workstation/src/styles.css`
  - 新增扫图短轨迹样式，区分 `扫图中`、`停止中`、`已停止`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展扫地式建图键盘流程测试，覆盖按住前无轨迹、按住后 `扫图中` 轨迹、松开后 `已停止` 轨迹和样式选择器。
- `docs/product/pc_tools_workstation.md`
  - 同步记录短轨迹的 WYSIWYG 口径和安全边界。

## 验证结果

- `npm test -- -t "keeps free-roam keyboard locked until map recording starts"`：通过，`1 passed | 191 skipped (192)`。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `npm test`：通过，`2 passed (2)`，`192 passed (192)`。
- `git diff --check`：通过，无空白错误。
- 全量测试会刷新 2026-06-11 两个旧 DOM smoke artifact 的 `checked_at`；本轮已恢复为基线时间戳，避免无关产物进入提交。

## 剩余风险

- 本轮只做 PC 前端 mock/静态验证，不触发真实小车运动，也不证明 HIL。
- 短轨迹按前端按住方向推导，不代表 SLAM/里程计真实轨迹；轨迹层本身不新增任何控制调用，真实扫地图效果仍以后续上车端地图刷新、HIL 和现场确认材料为准。
- Node 当前应继续监听 `0.0.0.0:7001`；本轮不修改 Clash、代理或系统网络配置。
