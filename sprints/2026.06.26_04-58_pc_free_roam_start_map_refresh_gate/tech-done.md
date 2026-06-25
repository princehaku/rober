# PC 扫图开始记录地图刷新 Gate

## sprint_type

micro

## 实际改动

- 扫地式建图 `开始扫地式建图` 接入地图 WYSIWYG gate。
- 地图画面或地图 proof 刷新中，普通地图卡 `重新建图` 和高级 `开始建图` 禁用。
- `startMapRuntime()` 在地图刷新中直接早退，不调用 `/api/map/start`。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`，1 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files / 191 tests passed。
- 通过：`git diff --check`。
- 已核对：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true` 显示 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 工作站前端/测试验证，没有触发真实 `/api/map/start`、manual、keyboard pulse、Nav2、delivery complete、stop 或 `/cmd_vel`。
- 真实上位机慢刷新期间的现场效果仍需操作确认；本轮 mock 已覆盖按钮禁用和函数早退。
