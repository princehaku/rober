# 2026-06-28 20:20 PC Ready 传感器自动进入建图启动

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增“摄像头和雷达都 ready”的建图目标态判断。
  - 当相机与雷达 ready 但地图记录尚未启动时，普通首屏自由移动卡片切到 `自动扫图` 目标。
  - 此时点击 `开始自动扫图（低速）` 不再直接按自由移动记录发起 start，而是先补地图记录和扫图画面刷新，再用 `confirm_mapping_active=true` 调用固定自动扫图代理。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 ready 传感器场景回归测试，锁定调用顺序为 `map/start -> free-roam/autonomy/start`。
  - 测试同时断言自动扫图请求体包含 `confirm_operator_safety=true` 和 `confirm_mapping_active=true`，且不调用 manual、Nav2 execute 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录“雷达和摄像头都 ready 后可以建图”的普通首屏交互口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "starts map recording before auto sweep"`
  - 结果：1 个测试文件通过，1 个目标测试通过，198 个测试按过滤跳过。
- 通过：`npm test -- --run test/App.test.ts -t "free-roam autonomy"`
  - 结果：1 个测试文件通过，10 个目标测试通过，189 个测试按过滤跳过。
- 通过：`npm test -- --run test/App.test.ts -t "starts low-speed free roam through the fixed proxy even when summary marks auto-sweep locked"`
  - 结果：1 个测试文件通过，1 个目标测试通过，198 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，347 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮验证范围是 PC 普通首屏 mock/单测链路，未向真实小车发送 free-roam、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel` 请求。
- 上车端仍会二次确认地图记录、相机和雷达 readiness；真实自动扫图 HIL 仍需要现场安全确认后单独验收。
