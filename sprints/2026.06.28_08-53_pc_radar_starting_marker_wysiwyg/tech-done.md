# PC 雷达启动中地图标记 WYSIWYG Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：雷达启动请求飞行中时，地图 marker 和扫描范围 aria 说明补充“旧点不当新点”，与启动后自动刷新 pending 的所见即所得口径一致。
- `pc-tools/workstation/test/App.test.ts`：更新雷达启动 pending 用例，锁定 marker 和扫描范围读屏说明，继续断言不会触发 manual、Nav2、delivery 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录雷达启动中地图标记不把旧点当实时点。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "map radar-starting marker"`，1 个测试通过，203 个同文件测试按筛选跳过。
- 通过：`npm test`，2 个 test files、352 个测试全部通过。
- 通过：`npm run lint`。
- 通过：`npm run build`；保留既有 Vite chunk 超过 500 kB 提示，构建成功。
- 通过：`git diff --check`。
- 复验说明：整理缩进后重新跑 targeted、lint、`git diff --check` 均通过；随后一次 `npm test` 全量在无关 wheel raw L/R 用例上偶发失败，单独复跑该用例通过，再次全量 `npm test` 通过 352/352。

## 剩余风险

- 本轮只改 PC 前端只读标记和测试，不连接真实雷达，不发送底盘、Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
