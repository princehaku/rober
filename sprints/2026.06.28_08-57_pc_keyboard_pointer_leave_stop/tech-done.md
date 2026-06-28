# PC 键盘拖出按钮停止 Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通键盘指南和自由移动提示补充“拖出按钮也会停”，和已有 `pointerleave` 停止行为一致。
- `pc-tools/workstation/test/App.test.ts`：新增屏幕方向键 `pointerleave` 用例，锁定拖出按钮会调用固定 stop 代理、方向归零、停止原因显示为“拖出屏幕方向键”，且不触发 Nav2 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 PC 连续手控的拖出停止边界。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "pointer leaves the button|keyboard control guide"`，1 个测试通过，204 个同文件测试按筛选跳过。
- 通过：`npm test`，2 个 test files、353 个测试全部通过。
- 通过：`npm run lint`。
- 通过：`npm run build`；保留既有 Vite chunk 超过 500 kB 提示，构建成功。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC 前端说明和测试，不连接真车，不发送真实 Nav2、delivery、free-roam start 或 `/cmd_vel`；测试中的 manual/stop 都是 mock。
