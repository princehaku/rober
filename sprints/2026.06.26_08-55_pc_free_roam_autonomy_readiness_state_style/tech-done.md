# PC 自动扫图准备面板状态外框

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 08:55

## 实际改动

- 普通首屏 `自动扫图准备` 面板将 `plainFreeRoamAutonomyReadiness.state` 暴露为外层 `data-state`。
- 新增 `未满足/待处理/已就绪` 面板状态外框样式，让上车端自动扫图 readiness 不只靠状态 chip 和长文案表达。
- 补充前端测试，锁定默认未满足、ready 但仍缺地图记录/地图刷新时的待处理、以及可启动自动扫图时的已就绪状态与 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该改动只影响 PC 前端 WYSIWYG，不自动启动自动扫图、不发送 manual/keyboard pulse、不执行 Nav2、delivery complete、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation"`，2 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node` 正在监听 `*:7001`。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实自动扫图状态机、真实键盘长按、真实底盘和真实 Nav2/delivery 未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
