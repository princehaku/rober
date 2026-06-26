# PC 行程失败原因同步到首屏进度

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增普通行程失败摘要，复用地图 marker 的短原因翻译。
  - 行程执行失败后，`行程操作`、`本轮进度`、验收卡点、送达前置检查和高级收口 checklist 同步显示 `最近行程未通过（规划失败/等待超时/执行失败）`。
  - 保持失败态只读展示，不自动重试、不执行 Nav2、不提交送达、不发送 manual/keyboard/stop。
- `pc-tools/workstation/test/App.test.ts`
  - 更新行程失败相关用例，锁定失败短原因在行程状态、本轮进度和 checklist 中可见。
- `docs/product/pc_tools_workstation.md`
  - 记录行程失败短原因同步到普通首屏进度与送达前置检查的契约。

## 验证结果

- `npm test -- -t "keeps the attempted visible route goal on the map when trip execution fails without goal coordinates|keeps failed plain trip visible when execution fallback has no key values|keeps latest failed trip visible in plain goal progress"`：通过，2 个用例通过，199 个用例按过滤条件跳过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍输出既有 chunk size warning，未新增构建错误。
- `npm test`：通过，2 个测试文件、201 个用例全部通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 仍监听 `*:7001`。
- 完整 `npm test` 会刷新两个旧 smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免提交无关测试副作用。

## 剩余风险

- 当前仅完成 PC 前端 mock 验证，不触发真实 Nav2 execute/latest 或真实路线 HIL。
