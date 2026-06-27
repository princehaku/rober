# PC 雷达停止请求 pending 所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `雷达停止中` 普通状态，用于高级 `radar/stop` 固定代理已发送但尚未返回的窗口；当前事实、地图 marker、地图 aria、雷达点口径和坐标口径不再把 stop pending 误说成刷新中。
- `pc-tools/workstation/src/styles.css`：把 `雷达停止中` 纳入雷达卡片、地图雷达扫描范围和地图雷达 marker 的 pending 视觉状态。
- `pc-tools/workstation/test/App.test.ts`：新增 radar stop 延迟回包测试，覆盖普通雷达卡、地图 marker、雷达点口径、当前事实和无 manual/free-roam/Nav2 控制请求。
- `docs/product/pc_tools_workstation.md`：同步记录 radar stop pending 的普通首屏契约。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows radar stop pending on the map while the fixed stop proxy is in flight"`，结果 `1 passed | 199 skipped`。
- 通过：`npm test`，结果 `2 passed`、`348 passed`。
- 通过：`npm run lint`，结果 `eslint .` 无报错。
- 通过：`npm run build`，结果 TypeScript 和 Vite build 成功；保留既有 Vite chunk size warning。
- 通过：`git diff --check`，无 whitespace/error 输出。

## 剩余风险

- 本轮只改 PC 端 radar stop pending 呈现，没有连接真实雷达或上车端验证停止效果。
- 本轮未触发 manual、keyboard、free-roam、Nav2、delivery、base stop 或 `/cmd_vel`。
- 工作区已有两份历史 artifact JSON 脏文件，本轮不使用、不修改、不提交。
