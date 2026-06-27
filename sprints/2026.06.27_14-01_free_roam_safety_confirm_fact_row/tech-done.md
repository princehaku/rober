# Free-roam safety confirm fact row

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏当前事实里的自由移动文案会同时看 `free_roam_autonomy_start_ready` 和本地安全确认。
  - 未勾安全确认时显示“勾安全确认后可启动”；勾上后才显示“可启动”。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖已勾安全确认和未勾安全确认两种 start-ready 文案。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 start-ready 事实条与最小安全确认的显示规则。

## 验证结果

- `npm test -- --run App.test.ts -t "start-ready free-roam|splits free movement"`
  - 结果：通过，`2 passed | 163 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`290 passed`。
- `npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning。
- live 只读验证：
  - `curl http://127.0.0.1:7001/api/robot-control/summary?...` 显示 `free_roam_autonomy=start_ready`、`free_roam_autonomy_start_ready=true`，runtime 为 `artifact_only=true/cmd_vel_publish_enabled=false`。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 PC Node 继续监听 `*:7001`。

## 剩余风险

- 本轮只调整 PC 普通首屏事实文案，不发送 free-roam start、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实自由移动仍需要现场勾选安全确认并点击开始。
