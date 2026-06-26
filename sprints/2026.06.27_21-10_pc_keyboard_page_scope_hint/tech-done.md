# PC 键盘全页非输入区手控文案锁定

## sprint_type

micro

## 实际改动

- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 的普通首屏与高级诊断键盘摘要：点击 `启用键盘` 后说明为“本页非输入区”可按住 W/A/S/D 或方向键连续手控，输入框内按键不会发车。
- 更新 `pc-tools/workstation/test/App.test.ts` 的键盘连续手控测试：锁定 ready/armed 文案包含“本页非输入区”，并把首次手控按键改为从 `document.body` 冒泡触发，证明不再要求焦点停在键盘小面板。
- 更新 `docs/product/pc_tools_workstation.md` 中仍保留的旧焦点口径，改为当前页面获得键盘控制权、非输入区可手控、可编辑控件内按键不发车。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "enables non-stop motion only after complete operator material"`，结果 `1 passed | 141 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts`，结果 `142 passed`。
- 通过：`git diff --check`，无 whitespace error 输出。

## 剩余风险

- 本轮只验证 PC 前端键盘事件范围和文案，不新增真实底盘运动证明。
- 真实上位机仍存在摄像头后端无帧、WAVE ROVER `T=1001` 反馈 L/R 仍为 `0/0` 的硬件/底盘执行风险；该风险已在上一轮诊断 sprint 留档。
