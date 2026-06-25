# PC 地图画面刷新口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图 caption 新增 `地图画面` 刷新口径。
  - 区分最近读取的真实地图、地图记录中未刷新、本轮扫图已刷新、按住扫图后已自动刷新、保存后待检查等状态。
  - 该口径只消费本地 map preview / free-roam 状态，不新增控制 endpoint，不发送 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖默认真实地图、地图记录中等待刷新、按住扫图自动刷新后的地图画面文案。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 普通首屏地图 WYSIWYG 刷新口径。

## 验证结果

- 通过：`npm test -- --testNamePattern "renders Robot Control V1 by default|sweeps map with the plain free-roam keyboard guide"`
  - 结果：`Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 168 skipped (169)`。
  - 说明：该 pattern 只命中默认首屏测试，未命中扫图测试名。
- 通过：`npm test -- --testNamePattern "keeps free-roam keyboard locked until map recording starts"`
  - 结果：`Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 168 skipped (169)`。
- 通过：`npm run lint`
  - 结果：`eslint .` 无报错。
- 通过：`npm test`
  - 结果：`Test Files 2 passed (2)`，`Tests 169 passed (169)`。
- 通过：`npm run build`
  - 结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过，Vite 输出 `✓ built`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮只增强 PC 地图画面的刷新口径，不证明真实 Nav2 路线执行、delivery success 或真车自动扫图。
- 地图 preview 仍是只读刷新结果，不是实时视频流；继续移动后必须再次刷新确认最新覆盖。
