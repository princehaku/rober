# PC 轮速保存失败状态收口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增轮速记录保存失败状态。
  - `保存轮速记录` 写入 operator report 失败后，轮速卡片显示 `保存失败`，按钮显示 `重试保存轮速记录`。
  - `本轮进度` 和 `验收卡点` 在保存失败时继续把轮速记录视为待完成，提示先重试保存，避免直接进入行程。
- `pc-tools/workstation/test/App.test.ts`
  - 新增保存轮速记录失败用例，覆盖普通首屏状态、重试按钮、进度提示和不误触发 Nav2/manual。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏轮速保存失败的用户可见契约和安全边界。

## 验证结果

- `npm test -- -t "keeps plain wheel evidence incomplete when saving the wheel record fails"`：通过，1 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 输出 chunk size warning，但构建成功。
- `npm test`：通过，2 test files passed，200 tests passed。
- 完整测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免无关 diff。

## 剩余风险

- 当前仅完成 PC 前端 mock 验证，不触发真实 first-jog、operator report 写入或 WAVE ROVER HIL。
