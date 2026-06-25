# PC 扫图键盘地图 Proof 刷新 Gate

## sprint_type

micro

## 实际改动

- 扫地式建图键盘 gate 从只看地图画面刷新扩展为统一地图 WYSIWYG gate。
- 地图 proof/状态刷新中，屏幕方向键禁用，保存地图继续禁用，不发送新的 manual/keyboard pulse。
- 扫图状态文案区分 `地图画面刷新中` 和 `地图状态刷新中`。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`，1 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files / 191 tests passed。
- 通过：`git diff --check`。
- 已核对：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true` 显示 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 工作站前端/测试验证，没有触发真实 manual/keyboard pulse、`/api/map/save`、Nav2、delivery complete、stop 或 `/cmd_vel`。
- 已经按住移动时仍允许松开或红色停止，这是停止兜底的有意保留；真实上位机 HIL 仍需现场确认。
