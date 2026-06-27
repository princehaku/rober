# 2026-06-28 16:40 PC 自由移动当前事实 pending 同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的自由移动/自动扫图行优先消费本地 free-roam start/stop pending、停止排队、start/stop 成功和失败回包。
  - 点击开始后不再继续显示旧 summary runtime 的“当前没有运动发布”；点击停止排队后显示“停止已排队”，停止回包后显示“停止请求已发送”。
  - 该改动只调整只读文案优先级，不新增 free-roam、manual、keyboard、Nav2、delivery、base stop 或 `/cmd_vel` 调用。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖自动扫图 start pending、stop queued、stop forwarded 三段 `当前事实` 文案。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步自由移动/自动扫图 `当前事实` WYSIWYG 口径。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首屏行为说明。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "queues free-roam autonomy stop while the start request is still pending"`
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

- 本轮未做真实小车 HIL；变更限定在 PC 首屏只读展示，不作为真实运动成功证明。
- 未发送任何真实 free-roam、manual、keyboard、Nav2、delivery、base stop 或 `/cmd_vel` 请求；真实小车运动状态仍需现场按安全流程验收。
