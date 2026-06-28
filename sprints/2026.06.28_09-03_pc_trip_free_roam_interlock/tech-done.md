# PC 行程中自由移动互锁 Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：Nav2 图上路线执行 pending 时，禁止扫图记录、地图保存、自由移动/自动扫图 start 和自由移动键盘启用；相关按钮显示 `行程中`，自动扫图下一步提示等待行程执行返回或先停止行程。
- `pc-tools/workstation/test/App.test.ts`：扩展现有 Nav2 pending WYSIWYG 用例，锁定自由移动/建图入口禁用，且强行触发 click 不会调用 map start 或 free-roam autonomy start。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录行程执行与自由移动/建图互锁边界。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "visible route goal as request-pending"`，1 个测试通过，204 个同文件测试按筛选跳过。
- 通过：`npm run lint`。
- 通过：`npm run build`；保留既有 Vite chunk 超过 500 kB 提示，构建成功。
- 通过：`git diff --check`。
- 通过：`npm test`，最终复跑 2 个 test files、353 个测试全部通过。
- 复验说明：第一次全量 `npm test` 在无关 `does not close wheel raw L/R from static nonzero base feedback samples` 用例上偶发失败；单独复跑该用例通过，再次全量复跑通过。

## 剩余风险

- 本轮只改 PC 前端互锁与 mock 测试，不连接真车，不发送真实 Nav2、manual、free-roam、map start 或 `/cmd_vel`。
