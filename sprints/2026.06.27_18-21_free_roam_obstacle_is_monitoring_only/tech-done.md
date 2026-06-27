# Free-roam obstacle is monitoring only

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自由移动近障碍提示从“原地换向避让，不继续直行”改成“建议原地换向避让；这只影响建图验收和直行策略，不阻塞低速自由移动”。
  - 保持现有安全边界：低速自由移动 start 仍只看现场安全确认、停止兜底和固定上车状态机入口；相机、雷达和近障碍只决定建图验收/运行监看口径。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 0.30m 和 live 0.04m 近障碍场景断言。
  - 新增/强化断言：live 0.04m 近障碍场景下，勾选安全确认后 `开始自由移动（低速）` 仍可用，不被雷达近障碍禁用。
- `docs/product/pc_tools_workstation.md`
  - 同步记录“近障碍是监看/直行策略，不阻塞自由移动启动”的 PC 口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "derives radar running state from runtime scan gates when lidar readback is missing"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 171 skipped (172)`
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "splits free movement from mapping acceptance when camera and radar are not ready"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 171 skipped (172)`
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`
  - `Tests 301 passed (301)`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - 仍有既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`git diff --check`

## 剩余风险

- 本轮没有触发真实小车运动；没有当前现场操作员安全确认时，仍不执行 free-roam/manual/keyboard/Nav2。
- live 相机仍是 DV20 UVC 无首帧；相机 ready 前可以自由移动，但不能按可验收建图收口。
- live Nav2 上次仍是 PWM action succeeded 但 wheel raw L/R=0/0；完整 Nav2 路线需要安全确认后用 ROS 重跑并复验 wheel raw L/R 非零。
