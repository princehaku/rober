# 2026-06-28 05:21 PC delivery 当前事实 pending 同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 增加送达 pending 行。
  - 读取 delivery latest/check 期间显示“正在读取最近行程和送达状态，不会发车；返回前不把旧送达记录当作当前结论”。
  - 提交最终送达确认期间显示“正在提交送达确认，不会发车；结果返回前先保持现场接管”。
  - 该改动只调整只读展示，不新增 delivery complete、operator report、Nav2、manual、keyboard、stop 或 `/cmd_vel` 请求。
- `pc-tools/workstation/test/App.test.ts`
  - 新增延迟 delivery latest 请求测试，锁定 pending 期间的 `当前事实` 文案，并确认不会误触发发车、送达确认或底盘运动。
- `docs/product/pc_tools_workstation.md`
  - 同步普通首屏 delivery pending WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows a current delivery fact while rereading delivery latest"`
  - 结果：1 个测试文件通过，1 个目标测试通过，192 个测试按过滤跳过。
- 通过：`npm test -- --run test/App.test.ts -t "shows delivery confirmation pending on the map while final completion is in flight"`
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

- 本轮未做真实小车 HIL；变更限定在 PC 首屏只读展示，不作为真实送达成功或完整 Nav2 行程完成证明。
- 未发送任何真实 delivery complete、operator report、Nav2 execute、manual、keyboard、base stop 或 `/cmd_vel` 请求；真实送达收口仍需现场按安全流程验收。
