# PC Current Fact Radar Deduplication

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `currentFactMapRadarParts`，在 `current_fact_plain` 中把地图主句和雷达 overlay 主句分层；地图 WYSIWYG 句带分号雷达诊断时，顶层事实只保留地图/路线/小车位置，雷达 marker 状态交给 overlay 主句说明。
- `pc-tools/workstation/test/catalog.test.ts`：补 stale radar overlay 场景断言，确认 `current_fact_plain` 中“已有雷达来源点 N 个”只出现一次。
- `docs/product/pc_tools_workstation.md`：记录当前事实拼句去重规则。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "radar"`，13 个相关测试通过，147 个跳过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite 构建通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提醒。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部通过。
- 通过：重启本机 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，live `current_fact_plain` 返回“地图画面、图上路线和小车位置已显示；雷达 marker 未贴到当前地图：当前显示 0 个点；旧来源点 81 个只作诊断。已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图”，旧来源点说明不再同时出现在地图主句和雷达主句里。

## 剩余风险

- 本轮只修 PC 首屏只读事实拼句，不启动雷达、不刷新地图、不改变实际 overlay 计算；live 当前雷达仍未运行，地图 marker 仍为 0。
