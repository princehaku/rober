# 轮速卡点确认后聚焦重试

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：现场点击 `已检查轮速卡点` 后，页面会把焦点移到 `检查后重试读非零 L/R` 试动按钮；若试动按钮仍不可用，则聚焦回 `轮速记录` 区域。该本地动作不调用任何机器人接口。
- `pc-tools/workstation/test/App.test.ts`：扩展 summary L/R=`0/0` 和 first-jog L/R=`0/0` 两个场景，验证本地卡点确认后聚焦重试试动按钮，且不新增请求。
- `docs/product/pc_tools_workstation.md`：同步轮速卡点确认后的普通首屏焦点规则。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、137 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，完成 app/server TypeScript 与 Vite production build。
- 通过：`git diff --check`。
- 已恢复 `npm test` 改写的历史 smoke JSON `checked_at` 副作用，提交范围不包含旧 artifacts 噪声。

## 剩余风险

- 本轮只改善 `L/R=0/0` 排查后的下一步引导，不证明 wheel raw L/R 非零。
- 真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和真实 PC 键盘连续手控仍需要现场操作和证据。
