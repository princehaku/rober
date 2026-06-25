# PC 扫图卡片内联方向键

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏“扫地式建图”卡片中新增内联方向键：前进、左转、右转、后退和停止。
  - 新按钮复用现有 keyboard manual pulse / release stop handler，不新增控制通道。
  - 未完成安全确认、地图记录和启用键盘扫图前，方向键保持 disabled。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 free-roam 测试，确认扫图卡片方向键初始禁用，启用后可按住前进并触发既有地图刷新/stop 收口流程。
- `docs/product/pc_tools_workstation.md`
  - 同步记录扫图卡片内联方向键的用户口径和安全边界。

## 验证结果

- 通过：`npm test -- --testNamePattern "keeps free-roam keyboard locked until map recording starts"`
  - 结果：`Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 169 skipped (170)`。
- 通过：`npm run lint`
  - 结果：`eslint .` 无报错。
- 通过：`npm test`
  - 结果：`Test Files 2 passed (2)`，`Tests 170 passed (170)`。
- 通过：`npm run build`
  - 结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过，Vite 输出 `✓ built`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮只提升 PC 端自由扫图操作入口；真实自动避障/自动覆盖/自动停止仍依赖上车端安全状态机和 HIL 证据。
- 内联方向键与原键盘面板共享同一状态机；真实运动仍要求现场 operator 持续观察并可随时停止。
