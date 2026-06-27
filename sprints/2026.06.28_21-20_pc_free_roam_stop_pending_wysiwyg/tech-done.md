# PC 自由移动停止请求 pending 所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：把 `free-roam/autonomy/stop` 请求尚未返回时的普通首屏按钮、当前事实、扫图状态和地图 marker 文案统一为“停止请求已发送，等待上车端返回；返回前未证明已停止”，避免把 pending 窗口误报成已经停止或正在停止完成态。
- `pc-tools/workstation/test/App.test.ts`：扩展自由移动停止失败回归测试，模拟 stop 请求挂起，覆盖按钮 `停止请求中`、地图 marker `auto_stopping`、当前事实、扫图状态、保存地图禁用和回包失败 fail-closed。
- `docs/product/pc_tools_workstation.md`：同步记录普通首屏 stop pending 契约，说明该呈现不新增 manual、keyboard、Nav2、delivery、map save 或 `/cmd_vel` 调用。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "blocks map save when free-roam autonomy stop fails"`，结果 `1 passed | 198 skipped`。
- 通过：`npm test`，结果 `2 passed`、`347 passed`。
- 通过：`npm run lint`，结果 `eslint .` 无报错。
- 通过：`npm run build`，结果 TypeScript 和 Vite build 成功；保留既有 Vite chunk size warning。
- 通过：`git diff --check`，无 whitespace/error 输出。

## 剩余风险

- 本轮是 PC 端 WYSIWYG 文案和 fail-closed 状态测试，未触发真实上车端 stop、manual、keyboard、Nav2、delivery、map save 或 `/cmd_vel`。
- 工作区已有两份历史 artifact JSON 脏文件，本轮不使用、不修改、不提交。
