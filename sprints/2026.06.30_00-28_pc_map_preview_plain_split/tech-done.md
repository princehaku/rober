# PC Map Preview Plain Split

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `RobotControlMapPreviewResponse` 中新增 `map_plain_hint` 和 `map_next_action_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`GET /api/robot-control/map/preview` 顶层 `plain_hint` 改为地图主句 + 雷达 overlay 主句的去重合成，`next_action_plain` 改为地图 WYSIWYG 下一步；路线相关下一步继续保留在 path/nav2 route overlay 字段。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：更新 map preview fixture 和断言，覆盖雷达 partial/not_current 与完整地图三类场景。
- `docs/product/pc_tools_workstation.md`：同步记录 map preview 顶层白话字段分层规则。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map preview"`，2 个相关测试通过，158 个跳过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite 构建通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提醒。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部通过。
- 通过：重启本机 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/map/preview`，live 返回 `plain_hint=地图画面、图上路线和小车位置已显示；雷达 marker 未贴到当前地图：当前显示 0 个点；旧来源点 81 个只作诊断...`，`map_plain_hint=地图画面、图上路线和小车位置已显示。`，`map_next_action_plain=先启动雷达，再刷新地图画面。`，`next_action_plain=先启动雷达，再刷新地图画面。`，同时 `path_preview_next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`

## 剩余风险

- 本轮只修 PC map preview 只读响应，不启动雷达、不刷新地图、不改变实际 overlay 计算；live 当前雷达仍未运行，地图 marker 仍为 0。
