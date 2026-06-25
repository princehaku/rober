# PC 扫图保存地图 WYSIWYG Gate

## sprint_type

micro

## 实际改动

- 普通首屏扫地式建图保存按钮接入地图 WYSIWYG gate。
- 地图画面或地图 proof 刷新中，扫图保存按钮显示 `等待地图刷新` 并禁用。
- 普通地图卡和高级诊断的 `保存地图` 在地图刷新中禁用，`saveMap()` 入口早退。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录刷新中不会调用 `/api/map/save` 或运动接口。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`，1 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files / 191 tests passed。
- 通过：`git diff --check`。
- 已核对：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true` 显示 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 工作站前端/测试验证，没有触发真实 `/api/map/save`、Nav2、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 未做真实上位机 HIL；扫图保存 gate 的现场效果仍需在真实上位机刷新慢或地图 proof 刷新中操作确认。
