# PC 键盘手控轮速读数保留

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘手控面板新增 `键盘轮速` 行。
  - 最近一次键盘 manual pulse 返回 wheel raw L/R 后，按住期间和松开停止后都会继续显示 `L/R` 与非零帧数。
  - 该行只消费已有 `remote_motion_key_values`，不新增请求、不发送额外 manual、stop、Nav2、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展扫地式建图屏幕方向键用例，验证键盘轮速行在按住和松开后都保留 `L/R=0.07/0.08` 与 `2` 帧非零。
- `docs/product/pc_tools_workstation.md`
  - 记录键盘轮速读数在普通首屏保留的产品边界。

## 验证结果

- `npm test -- -t "free-roam|keyboard"`：通过，2 files / 12 passed / 164 skipped。
- `npm run lint`：通过。
- `npm run build`：通过，Vite production build 和 server TypeScript build 均完成。
- `npm test`：通过，2 files / 176 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node 90259 ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮不触发真实 Nav2、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 轮速读数仍取决于上位机固定 manual 代理是否返回 `remote_motion_key_values`；没有返回时普通首屏不显示该行。
