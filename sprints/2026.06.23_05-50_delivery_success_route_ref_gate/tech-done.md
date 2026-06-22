# Delivery Success Route Ref Gate

## sprint_type

micro

## 目标

- 继续推进 PC 端四项收口目标中的 `delivery success`，避免 `delivery/latest` 的旧行程材料把本轮送达误判为完成。
- 不调用 subagent；不发送真实运动、Nav2 执行或送达确认请求。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 delivery success 与本轮 Nav2 execution ref 的一致性检查。
  - `delivery/latest` 若携带的 route/map ref 不等于当前未过期 Nav2 `evidence_ref`，普通首屏和高级目标收口都保持 `送达确认待完成`。
  - 普通首屏新增“送达成功记录的行程材料不是本轮记录”提示，不暴露 `route_map_ref` 或接口字段。
- `pc-tools/workstation/test/App.test.ts`
  - 新增回归测试覆盖“新鲜 Nav2 成功 + 新鲜 delivery_success + 旧 route/map ref”场景。
  - 断言不会调用 operator report、delivery complete、Nav2 execute 或 manual。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-23 05:50 起的 delivery success route ref gate。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 135 passed (135)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- 通过：`git diff --check`

## 剩余风险

- 该轮只修 PC 端收口误判，不证明真实车已完成 wheel raw L/R 非零、完整 Nav2 路线执行、送达成功或键盘连续手控。
- 若后端旧版本完全不返回 delivery material route/map ref，则 PC 只能退回时间新鲜度 gate；本轮不会因此自动确认送达。
