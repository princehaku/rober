# Plain Goal Progress

sprint_type: micro

## 实际改动

- PC 普通首屏 `移动/导航` 卡片新增“本轮进度”，用普通话术展示四项目标状态：轮速记录、行程执行、送达确认、键盘手控。
- 轮速记录消费已读 wheel L/R 非零材料或 first-jog/manual 结果；行程执行消费最近行程成功结果；送达确认消费 delivery gate；键盘手控消费现有手控 gate。
- 首屏文案避免 `Nav2`、`proof`、`HIL`、`/api/base/manual` 等工程字段，完整证据仍留在高级诊断。
- 更新 Vue 测试，覆盖“本轮进度”四项显示、默认键盘未满足提示、条件满足后键盘手控显示 `可使用`。
- 本轮不发真实运动、不提交送达确认、不改变后端安全 gate。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`113 passed (113)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 只读现场证据

- SSH 上位机 `root@192.168.1.11 -p 37878` 可达。
- `/api/base/status` 可读到 `/dev/ttyS5`、115200、`T=1001`，但本次只读窗口 L/R 仍是 `0/0`，不证明 wheel raw L/R 非零。
- `/api/nav2/proof/latest` 已显示路径生成链路可读，最近 `/api/nav2/goal/execution/latest` 有 action 材料；本轮不触发新的 Nav2 执行。
- `/api/delivery/latest` 与 `/api/operator/report` 仍显示 delivery success 未完成，latest operator report 是送达草稿材料，不是现场最终确认。

## 剩余风险

- 完整目标仍未完成：wheel raw L/R 非零、完整 Nav2 路线执行和 delivery success 需要现场安全确认与真实执行证据。
- 本轮只是把缺口放到普通首屏，减少误判和查找成本。
