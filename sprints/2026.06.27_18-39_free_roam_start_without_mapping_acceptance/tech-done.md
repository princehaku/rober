# 自由移动 start 不绑定建图验收

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自由移动模式下，自动状态机补证按钮不再把“开始记录（不发车）”当作前置目标；缺停止兜底时指向停止兜底，否则显示 `检查自由移动条件`。
  - 自动状态机补证焦点在自由移动模式下优先指向低速自由移动/键盘条件，不把地图记录作为相机未 ready 时的前置条件。
  - `mapping_active_requested=false` 的 start 回包也会在参数写入摘要里明确显示 `本轮只按自由移动记录`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增回归：相机首帧未出、建图缺口存在、地图记录未启动时，勾选安全确认后 `开始自由移动（低速）` 直接调用固定 free-roam start 代理，body 为 `confirm_operator_safety=true`、`confirm_mapping_active=false`；不调用 map start、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 2026-06-27 18:39 口径：自由移动 start 和建图验收分层，只有画面/雷达/地图记录/新地图画面都 ready 时才声明 `confirm_mapping_active=true`。

## 验证结果

- 已通过：`npm test -- --run test/App.test.ts -t "free movement"`，2 passed / 172 skipped。
- 已通过：`npm test -- --run`，2 test files passed，303 tests passed。
- 已通过：`npm run build`。Vite 仍输出既有 chunk >500 kB 警告，不影响本轮通过。
- 已通过：`npm run lint`。
- 已通过：`git diff --check`。

## 剩余风险

- 本轮没有触发真实 free-roam start、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`；真实低速自由移动仍需要现场 operator 勾选安全确认并显式点击。
- 当前 live 摄像头仍是 UVC 首帧超时且非独占，因此即使自由移动可启动，本轮仍不能按可验收建图收口。
