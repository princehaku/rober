# PC 行程操作面板状态外框

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 08:40

## 实际改动

- 普通首屏 `行程操作` 面板将当前 `plainTripSummary.state` 暴露为外层 `data-state`。
- 新增 `已准备/执行中/准备中/读取中/停止中/停止已发送/待确认/待准备/需复验/需检查/执行失败` 等状态外框样式，让 Nav2 图上路线可执行、执行中、异常状态在面板层也所见即所得。
- 补充前端测试，锁定图上路线已可执行和 Nav2 execute pending 两条路径的面板 `data-state` 与 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该改动只影响 PC 前端 WYSIWYG，不自动执行 Nav2、不发送 manual/keyboard pulse、delivery complete、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "draws no-motion route start and end markers when no executed goal is available|marks the visible route goal as executing while the plain trip request is pending"`，2 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node` 正在监听 `*:7001`。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实 Nav2、真实底盘、真实键盘手控和真实 delivery complete 未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
