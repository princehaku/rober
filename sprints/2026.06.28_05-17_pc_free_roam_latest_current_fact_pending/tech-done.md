# 2026-06-28 05:17 PC free-roam latest 当前事实 pending 同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的自由移动行优先消费 `freeRoamAutonomyLatestPending`。
  - 刷新最新上车自由移动状态期间显示“正在读取最新上车状态，返回前不把旧自由移动记录当作当前结论”，避免旧 artifact-only、旧停止或旧运行记录冒充当前状态。
  - 该改动只调整只读展示，不新增 latest、free-roam start/stop、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel` 请求。
- `pc-tools/workstation/test/App.test.ts`
  - 在“刷新自由移动状态（只读）”测试里加入延迟 latest 请求，锁定 pending 期间的 `当前事实` 文案。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首屏 free-roam latest pending WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "refreshes free-roam autonomy latest as a read-only first-screen action"`
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

- 本轮未做真实小车 HIL；变更限定在 PC 首屏只读展示，不作为真实自由移动或自动扫图运行证明。
- 未发送任何真实 free-roam start/stop、manual、keyboard、Nav2、delivery、base stop 或 `/cmd_vel` 请求；真实运动状态仍需现场按安全流程验收。
