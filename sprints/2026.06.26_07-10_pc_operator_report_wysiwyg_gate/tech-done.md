# 2026.06.26 07:10 PC operator report WYSIWYG gate

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `恢复试动确认` 改为统一使用 `canRestorePlainFirstJogMaterial`：等待 WebRTC 画面打开/关闭完成、地图 proof/preview 刷新完成、operator report 空闲后才允许写入 latest operator report。
  - 普通首屏 `保存轮速记录` 改为统一使用 `canSavePlainWheelEvidence`：地图 proof/preview 正在刷新时按钮显示 `等待地图刷新` 并同步禁止 handler 写入。
  - 两个 handler 入口都复用 computed gate，避免按钮禁用态和实际点击逻辑漂移。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展恢复 first-jog 材料测试：地图 preview pending 时两个恢复按钮显示 `等待地图刷新`、禁用，点击不产生 operator report。
  - 扩展保存 wheel raw L/R 证据测试：地图 preview pending 时保存按钮显示 `等待地图刷新`、禁用，点击不产生 operator report。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-26 07:10 起普通首屏 operator report 写入动作的画面/地图 WYSIWYG gate。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "restores first-jog material from existing visual refs without sending motion|summarizes first-jog wheel evidence on the plain first screen after a forwarded trial"`，2 passed / 190 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 files / 192 passed。
- 通过：`git diff --check`。
- 已确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true` 输出 `node ... TCP *:7001 (LISTEN)`。
- 已处理：完整 `npm test` 只改动两个 2026-06-11 旧 DOM smoke artifact 的 `checked_at`，已恢复到原始基线时间戳，未纳入提交。

## 剩余风险

- 本轮只做 PC 端 mock/组件验证，不触发真实小车运动，不等同 HIL 或真实 WAVE ROVER 串口验证。
- 本轮没有改 Clash、系统代理或上车端端口配置。
