# sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts` 的 Nav2 execution key values 新增 `evidence_ref`，供 PC UI 作为送达 `route_map_ref` 候选。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 在默认关闭的 `高级诊断 -> Nav2 规划详情` 新增送达材料快捷表单：
  - `operator evidence ref`
  - `送达视频 ref`
  - `route/map ref`
  - `使用最近 Nav2 ref`
  - 显式送达确认 checkbox
  - `提交送达材料并确认（高级）`
- 快捷入口先走固定 `POST /api/robot-control/operator/report?baseUrl=...` 提交 operator report，再在 report 成功后走固定 `POST /api/robot-control/delivery/complete?baseUrl=...`。它不执行 Nav2、不调用 manual/stop、不发布 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md` 同步说明快捷入口的材料要求和边界。

## 验证结果

- `cd pc-tools/workstation && npm test` 通过，100 tests。
- `cd pc-tools/workstation && npm run lint` 通过。
- `cd pc-tools/workstation && npm run build` 通过。
- `git diff --check` 通过。
- 重启本机 `npm run api` 后只读 smoke 通过：
  - `GET http://127.0.0.1:8787/api/health` 返回 HTTP 200，`delivery_success=false`。
  - `GET http://127.0.0.1:8787/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，`console_status=blocked`、`delivery_success=false`。
  - `GET http://192.168.1.11:8787/api/delivery/latest` 返回 HTTP 200，`delivery_success=false`、`status=blocked_missing_delivery_material`，缺项仍包括 operator report、delivery claim、route_map_ref 和 visual ref。

## 剩余风险

- 本轮没有提交真实送达 operator report，因为当前会话没有现场视频/投放确认材料；delivery gate 仍应保持 blocked。
- 该入口降低了现场收口操作成本，但真实 `delivery_success=true` 仍必须由现场人员提供可复核视频与 route/map ref 后才能成立。
