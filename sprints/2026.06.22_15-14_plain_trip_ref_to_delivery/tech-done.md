# Plain Trip Ref To Delivery

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 普通首屏 `执行行程` 成功后，自动把本次行程 evidence ref 填入送达材料候选，减少 delivery success 前的手工复制步骤。
- `任务收口` 的送达材料状态新增 `待画面`，用于表达“行程材料已在，还需要补视频/相机材料”。
- 补测试确认该自动回填不会提交 operator report、不会调用 delivery complete，也不会触发 manual 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md` 记录新的普通流程。

## 验证结果

- 通过：`npm test`，2 个 test files、117 个 tests 全部通过。
- 通过：`npm run lint`。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只减少 PC 首屏送达材料准备步骤；真实完整 Nav2 路线执行仍需现场显式点击 `执行行程` 并由上位机返回 `goal_succeeded`。
- 本轮不自动采集画面、不提交送达草稿、不确认 delivery success。
