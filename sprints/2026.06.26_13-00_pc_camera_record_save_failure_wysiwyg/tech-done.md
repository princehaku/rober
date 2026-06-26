# PC 当前画面记录保存失败 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `用当前画面记录` 已读到 camera probe 样张但 operator report 保存失败时，普通首屏实时画面卡显示 `失败`。
  - 画面框和 `画面状态` 同步显示 `画面已读到，但记录保存失败：<原因>`，避免回落成“相机在线但未打开”。
  - 当前画面记录按钮在该状态下显示 `重试记录当前画面`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 camera probe 成功、operator report 保存失败用例，锁定相机卡失败态、重试按钮和不误触发 first-jog/manual/Nav2/delivery。
- `docs/product/pc_tools_workstation.md`
  - 记录当前画面记录保存失败的首屏 WYSIWYG 契约和安全边界。

## 验证结果

- `npm test -- -t "keeps camera record save failure visible on the plain camera card"`：通过，1 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 输出 chunk size warning，但构建成功。
- `npm test`：通过，2 test files passed，201 tests passed。
- 完整测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免无关 diff。

## 剩余风险

- 当前仅完成 PC 前端 mock 验证，不触发真实 camera probe、operator report 写入或真实上车画面。
