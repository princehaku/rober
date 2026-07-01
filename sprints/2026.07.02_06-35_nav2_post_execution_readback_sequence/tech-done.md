# 2026-07-02 06:35 Nav2 执行后验收读回序列

sprint_type: micro

## 实际改动

- 普通首屏 `执行图上路线` 在 execution forwarded 后，改为按 `nav2_route_acceptance_packet.readback_endpoints` 自动刷新执行后验收材料。
- 新增 Nav2 执行后只读读回执行器，白名单固定为地图预览、Nav2 latest、底盘 feedback samples、delivery latest 和 summary；地图预览保留 `tripExecutionRefresh` 标记。
- App 测试补充执行后请求顺序断言：execute 之后必须拉地图、latest、轮速、送达和 summary，且不发送 manual、`/cmd_vel`、delivery complete、stop 或其他运动入口。
- 同步 PC 工具文档，明确执行后读回是自动验收刷新，不是额外发车。

## 验证结果

- 已通过：`git diff --check`
- 已通过：`cd pc-tools/workstation && npm test -- App.test.ts`，结果 `Test Files 1 passed`，`Tests 236 passed`。
- 已通过：`cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts`，结果 `Test Files 3 passed`，`Tests 427 passed`。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响本轮合同。
- 待补充：提交和推送。

## 剩余风险

- 本轮没有执行真实 Nav2 行程、真实键盘手控或真实自由移动；只增强真实执行成功后的 PC 自动验收读回链路。
