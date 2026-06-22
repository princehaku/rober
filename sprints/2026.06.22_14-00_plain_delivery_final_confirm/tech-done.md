# Plain Delivery Final Confirm

sprint_type: micro

## 实际改动

- PC 普通首屏 `任务收口` 新增“最终确认”小面板，把原本只在高级诊断里的送达最终确认搬到普通用户路径。
- 面板默认不勾选；`确认送达` 按钮只有在送达材料已准备、七项最终确认都勾选、且当前无 pending 请求时才可点击。
- 普通入口复用既有 `submitDeliveryOperatorReportAndComplete`，先提交 operator report，再调用固定 delivery complete gate；不新增后端绕行路径。
- 首屏文案避免 `Nav2/proof/HIL/ref/API` 等工程字段，完整证据和字段仍保留在高级诊断。
- 更新 Vue 测试，覆盖默认禁用、准备材料后仍禁用、保存草稿不触发 complete、七项勾全后普通首屏提交 operator report + delivery complete，且不调用 Nav2 goal、base manual 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`113 passed (113)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 剩余风险

- 本轮只把 delivery success 的人工最终确认入口放到普通首屏，并未替 operator 勾选或提交真实送达确认。
- 真实 delivery success 仍需要现场人员确认送达并由上位机 delivery gate 返回成功。
- wheel raw L/R 非零和完整 Nav2 路线执行仍需要现场安全确认与真实执行证据。
