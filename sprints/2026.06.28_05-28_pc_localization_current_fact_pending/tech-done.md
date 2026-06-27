# 2026-06-28 05:28 PC 重新定位当前事实 pending 同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的地图行优先消费 `localizationResetPending`。
  - 点击 `重新定位` 后，在固定 localization reset 代理返回前显示“正在重新定位，小车地图位置刷新中；返回前不把旧位置当作当前定位”。
  - 旧地图画面仍可见时继续说明当前仍显示地图画面，避免把旧机器人位置误当成当前定位。
- `pc-tools/workstation/test/App.test.ts`
  - 新增延迟 localization reset 测试，锁定 pending 期间的 `当前事实` 文案，并确认不会误触发 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步普通首屏重新定位 pending WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows localization reset pending in current map facts"`
  - 结果：1 个测试文件通过，1 个目标测试通过，193 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，341 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实小车 HIL；变更限定在 PC 首屏只读展示，不作为真实定位成功或地图坐标正确证明。
- 未发送任何真实 Nav2 execute、manual、keyboard、delivery、base stop 或 `/cmd_vel` 请求；真实定位和行程执行仍需现场按安全流程验收。
