# PC Keyboard Free-Move Map Marker Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：键盘按住方向时，地图方向 marker 不再要求地图记录已启动。
  未启动地图记录时显示 `自由移动方向`；已启动地图记录时继续显示 `扫图方向`。扫图短轨迹仍只在地图记录中出现，避免把自由移动伪造成建图材料。
- `pc-tools/workstation/test/App.test.ts`：补充自由移动模式下按住屏幕方向键的回归断言，锁定地图 marker、raw L/R、无扫图短轨迹和不触发 `/cmd_vel` 的边界。
- `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`：同步记录 PC 键盘自由移动地图所见即所得口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "splits free movement from mapping acceptance when camera and radar are not ready"`
  - 结果：1 passed，203 skipped。
- 通过：`cd pc-tools/workstation && npm test`
  - 结果：2 files passed，352 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`
  - 结果：`eslint .` 无错误。
- 通过：`cd pc-tools/workstation && npm run build`
  - 结果：TypeScript 与 Vite build 通过；Vite 仍提示单 chunk 超过 500 kB 的既有体积 warning。
- 通过：`git diff --check`
  - 结果：无 whitespace error。

## 剩余风险

- 本轮没有连接真实小车执行键盘手控，只用 PC/Vitest fixture 验证 UI 与代理调用边界。
- 自由移动 marker 是本机按住状态，不是里程计轨迹；未启动地图记录时仍不会画扫图短轨迹。
