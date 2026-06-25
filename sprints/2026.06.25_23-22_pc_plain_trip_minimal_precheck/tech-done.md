# PC 普通行程最小预检

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `行程操作` 移除 `可选复查（不发车）` 按钮。
  - 普通首屏行程状态话术改为“已勾安全确认；可以准备图上路线”，避免把可选 preflight 表达成发车前必做步骤。
  - `目标收口进度 -> 去行程` 不再落到 preflight 控件，只聚焦安全确认、准备路线、执行路线或读取结果。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏行程测试，断言 `plain-trip-preflight` 不存在。
  - 保留“未看到图上路线时执行按钮禁用、不调用 Nav2 execute、不调用 manual 或 `/cmd_vel`”的安全断言。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏最小预检口径：只勾现场安全确认，preflight 下沉到高级诊断。

## 验证结果

- 通过：`npm test -- -t "plain trip|minimal trip|trip controls safety-gated|route is visible"`（7 passed，165 skipped）
- 通过：`npm run lint`
- 通过：`npm test`（172 passed）
- 通过：`npm run build`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`（`node` 监听 `*:7001`，未使用 Clash 端口）

## 剩余风险

- 本轮是 PC 普通 UI 精简，没有触发真实 Nav2 execute 或真实底盘运动。
- 完整发车仍依赖上位机固定 `nav2/goal/execute` gate、当前地图路线 WYSIWYG 和现场 operator 确认。
