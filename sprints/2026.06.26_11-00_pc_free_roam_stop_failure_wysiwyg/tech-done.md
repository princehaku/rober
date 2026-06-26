# 2026-06-26 11:00 PC 扫地式建图停止失败 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 扫地式建图识别 `blocked_keyboard_stop_failed`，停止失败后扫图卡片进入失败态，下一步提示转为点红色停止。
  - 停止失败后保存 gate fail-closed，`保存当前地图` 改为 `先停止小车` 并保持禁用。
  - 地图 action marker 和短轨迹新增 stop failure 状态，避免失败后误显示为已停可保存。
- `pc-tools/workstation/src/styles.css`
  - 为 `plain-map-free-roam-action-marker[data-state="stop_failed"]` 和 `plain-map-free-roam-trail[data-state="停止失败"]` 增加警示视觉态。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 stop proxy rejected 的扫地式建图回归，锁定卡片、地图 marker、短轨迹、保存 gate 和安全边界。
- `docs/product/pc_tools_workstation.md`
  - 同步记录扫地式建图 stop failure 的 WYSIWYG 口径和安全边界。

## 验证结果

- `npm test -- -t "shows free-roam keyboard release while stop is still pending|keeps free-roam map fail-closed when keyboard release stop fails"`：通过，2 passed / 192 skipped。
- `npm run lint`：通过。
- `npm run build`：通过，Vite production build 完成。
- `npm test`：通过，2 files / 194 tests passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮只做 PC 前端 mock/静态验证，不触发真实底盘 stop、真实 Nav2 或真实建图 HIL。
- `停止失败` 只表示 PC stop proxy 未证明停止成功；真实小车是否静止仍需现场观察、后端 readback 和 HIL 材料确认。
- Node 当前应继续监听 `0.0.0.0:7001`；本轮不修改 Clash、代理或系统网络配置。
