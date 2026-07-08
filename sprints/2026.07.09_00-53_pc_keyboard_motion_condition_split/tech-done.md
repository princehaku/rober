# PC 键盘移动与条件读回拆分

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘手控 readiness 从 summary 合同/扫图 runtime 中拆出来，只保留默认小车地址、现场安全默认确认和 Nav2 行程占用三类移动前置。
  - 自由移动/扫图卡片未启动地图记录时也允许按住方向键，下一步聚焦键盘面板，不再回到“先开始扫图记录”。
  - 每次键盘 manual pulse 成功转发后记录 PC 本地点位；有 map-frame 位姿时在地图上画点和折线，缺位姿时只保留待定位记录，不伪造 SLAM 轨迹。
  - W/A/S/D 组合方向变化不再被当前 pulse in-flight 的通用 pending gate 拦住，下一拍直接使用新方向。
- `pc-tools/workstation/src/styles.css`
  - 新增 PC 手动点位地图覆盖层样式。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 summary 合同缺失时仍可通过固定 manual 代理移动。
  - 覆盖未启动地图记录时自由移动键盘可用、会记录本地点位、短轨迹可见。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 同步当前键盘 stop trigger 和 W+A 组合转弯文案合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录“移动与条件读回拆分”和本地点位记录边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm run test -- App.test.ts`，245 tests。
- 通过：`cd pc-tools/workstation && npm run test`，3 files / 459 tests。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`HOST=0.0.0.0 PORT=7001 npm run api` 已重启 PC Node，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`。
- 通过：`curl http://127.0.0.1:7001/` 返回新构建资源 `assets/index-D7XuXmFQ.js`，bundle 内可检索到 `按住方向键记录点位`、`keyboard-manual-map-point-summary`、`plain-map-keyboard-manual-points`。
- 通过：`curl http://127.0.0.1:7001/api/robot-control/summary` 返回 `readable`、`bounded_repeating_manual_pulse`、`key_release_all|window_blur|page_hidden|stop_button`。

## 剩余风险

- 本轮是 PC/Vitest/打包验证，未在真实车上长按方向键做 HIL 复验。
- PC 本地点位只用于普通用户扫图前后复盘；它不是正式 SLAM、里程计或 Nav2 costmap 轨迹。
- wheel raw `T=1001 L/R` 非零、完整 Nav2 路线执行和 delivery success 仍需后续真实现场验收。
