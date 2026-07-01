# Summary 顶层地图 WYSIWYG Alias

## sprint_type

micro

## 实际改动

- 在 `GET /api/robot-control/summary` 顶层补齐 `map_current_visible`、`path_current_visible` 和 `live_wysiwyg_map_visible`。
- 三个 alias 均与 `live_closure_summary` 同名字段同源，方便现场 `curl | jq` 直接判断地图底图、图上路线和地图 WYSIWYG 是否可见。
- 同步 TypeScript 合同、summary/catalog 测试和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `git diff --check`：通过。
- `npm test -- --run test/robotControlSummary.test.ts -t "WYSIWYG"`：未匹配到测试名，1 file / 9 tests skipped；不作为通过证据。
- `npm test -- --run test/robotControlSummary.test.ts`：通过，9 passed。
- `npm test -- --run test/catalog.test.ts -t "live-summary"`：通过，1 passed / 180 skipped。
- `npm test`：通过，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：新 Node PID `58506` 监听 `*:7001`。
- 只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：顶层返回 `map_current_visible=true`、`path_current_visible=true`、`live_wysiwyg_map_visible=true`、`camera_current_visible=false`、`radar_map_points_visible=false`、`live_wysiwyg_missing_surface_ids=["camera","radar_map_points"]`。

## 剩余风险

- 本轮只补只读 alias；不执行 Nav2、键盘、自由移动、建图、送达或 stop，不验证真实运动闭环。
