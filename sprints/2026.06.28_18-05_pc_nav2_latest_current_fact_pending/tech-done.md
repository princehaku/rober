# 2026-06-28 18:05 PC Nav2 latest 当前事实 pending 同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的行程行优先消费 `navGoalExecutionLatestPending`。
  - 读取最近行程结果期间显示“正在读取最近行程结果，返回前不把旧结果当作当前结论”，避免旧到达记录继续冒充当前结论。
  - 该改动只调整只读展示，不新增 latest、Nav2 execute、delivery、manual、keyboard、stop 或 `/cmd_vel` 请求。
- `pc-tools/workstation/test/App.test.ts`
  - 在“重新读取最近 Nav2 goal 结果”pending 测试里，锁定 `当前事实` 同步显示 latest pending。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首屏 Nav2 latest pending WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows a map-level pending state while rereading the latest Nav2 goal result"`
  - 结果：1 个测试文件通过，1 个目标测试通过，191 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，339 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实 Nav2 或真实小车 HIL；变更限定在 PC 首屏只读展示，不作为真实行程执行成功证明。
- 未发送任何真实 latest、Nav2 execute、delivery、manual、keyboard、base stop 或 `/cmd_vel` 请求；真实行程状态仍需现场按安全流程验收。
