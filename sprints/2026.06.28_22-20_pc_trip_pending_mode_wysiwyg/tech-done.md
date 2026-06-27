# PC 图上路线执行 pending 控制模式所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：图上路线执行 pending 的目标文案追加 `本次用 ROS/SPEED/PWM`，来源与实际 execute 请求 body 的 `base_command_mode` 保持一致。
- `pc-tools/workstation/test/App.test.ts`：更新图上路线 pending/stop pending 回归测试，覆盖行程卡、当前事实、行程进度和地图执行 caption 都显示 `本次用 ROS`，并继续断言请求 body 为 `base_command_mode: "ros"`。
- `docs/product/pc_tools_workstation.md`：同步记录执行 pending 控制模式 WYSIWYG 契约。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "marks the visible route goal as request-pending while the plain trip request is pending"`，结果 `1 passed | 199 skipped`。
- 通过：`npm test`，结果 `2 passed`、`348 passed`。
- 通过：`npm run lint`，结果 `eslint .` 无报错。
- 通过：`npm run build`，结果 TypeScript 和 Vite build 成功；保留既有 Vite chunk size warning。
- 通过：`git diff --check`，无 whitespace/error 输出。

## 剩余风险

- 本轮只改 PC 端 pending 文案和测试，没有真实执行 Nav2 路线或验证上车端运动结果。
- 本轮未新增 Nav2 execute、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel` 调用。
- 工作区已有两份历史 artifact JSON 脏文件，本轮不使用、不修改、不提交。
