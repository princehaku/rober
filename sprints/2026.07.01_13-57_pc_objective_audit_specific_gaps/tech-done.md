# PC Objective Audit Specific Gaps

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`objective_audit_summary_plain` 的未完成列表改为当前具体缺口表达。当前地图/雷达点已可见但相机未显示时，顶层摘要写“画面未显示”，不再用“画面/地图/雷达点”大类掩盖已完成的地图和雷达事实；建图缺口写“建图启动还差画面首帧”。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：锁定雷达/地图已完成、相机未完成场景，确认顶层目标摘要不再包含“画面/地图/雷达点”或“雷达点未贴图”。
- `docs/product/pc_tools_workstation.md`：同步 objective audit 顶层摘要必须使用具体缺口的产品合同。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，结果 `1 passed`、`8 passed`。
- 通过：`git diff --check`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 仍提示主 chunk 超过 500 kB，这是既有体积警告，不影响本轮目标摘要文案。
- 通过：`npm test`，结果 `3 passed`、`420 passed`。
- 通过：重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 Node `*:7001`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：真实只读 `GET /api/robot-control/live-summary` 返回 `objective_audit_summary_plain="四项目标完成 1/4；下一项：行程/键盘/自由移动；未完成：行程/键盘/自由移动、画面未显示、建图启动还差画面首帧。"`，同时 `live_wysiwyg_missing_surface_ids=["camera"]`、`radar_overlay_status=loaded`、`mapping_start_missing_reasons=["camera_first_frame"]`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`publishes_cmd_vel=false`。

## 剩余风险

- 本轮只修 PC 只读目标摘要，不执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 真实相机首帧仍未 ready，顶层摘要应继续显示画面缺口；完整运动闭环仍需现场安全确认后验证。
