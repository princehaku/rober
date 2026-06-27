# 2026-06-28 05:24 PC 行程路线准备当前事实 pending 同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的行程行优先消费 `nav2RefreshPending`。
  - 点击 `准备图上路线` / `刷新图上路线` 后，在 no-motion Nav2 proof refresh 返回前显示“正在准备图上路线，不会发车；返回前不把旧路线当作当前可执行路线”。
  - 该改动只调整只读展示，不新增 Nav2 execute、manual、keyboard、delivery、stop 或 `/cmd_vel` 请求。
- `pc-tools/workstation/test/App.test.ts`
  - 在延迟 no-motion Nav2 proof refresh 的行程准备测试里，锁定 pending 期间的 `当前事实` 文案，并继续确认不会触发 Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步普通首屏行程路线准备 pending WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "refreshes the map automatically after plain trip preparation so the route becomes visible"`
  - 结果：1 个测试文件通过，1 个目标测试通过，192 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，340 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实小车 HIL；变更限定在 PC 首屏只读展示，不作为真实 Nav2 路线执行成功证明。
- 未发送任何真实 Nav2 execute、manual、keyboard、delivery、base stop 或 `/cmd_vel` 请求；真实行程执行仍需现场按安全流程验收。
