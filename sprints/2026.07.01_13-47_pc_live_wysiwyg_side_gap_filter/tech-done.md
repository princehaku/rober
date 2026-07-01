# PC Live WYSIWYG Side Gap Filter

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`live_closure_summary` 的 `side_blocker_ids` / `side_gap_summary_plain` 现在按同一次 live WYSIWYG 当前事实过滤已经满足的画面、地图和雷达侧边缺口；如果雷达点当前已贴图，就不再把“雷达点贴到地图”继续显示成其它缺口。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：补充雷达 overlay 已加载场景，确认 `live_wysiwyg_missing_surface_ids`、`side_blocker_ids` 和 `side_gap_summary_plain` 不再包含雷达贴图缺口，同时建图缺口仍保留。
- `docs/product/pc_tools_workstation.md`：同步当前所见摘要过滤合同和 no-motion 边界。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，结果 `1 passed`、`7 passed`。
- 通过：`git diff --check`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 仍提示主 chunk 超过 500 kB，这是既有体积警告，不影响本轮当前所见摘要过滤。
- 通过：`npm test`，结果 `3 passed`、`419 passed`。
- 通过：重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 Node `*:7001`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：真实只读 `GET /api/robot-control/live-summary` 在雷达 `not_current` 时保留 `side_blocker_ids=["camera_wysiwyg","radar_map_points_wysiwyg","mapping_start"]`，这是正确的当前缺口。
- 通过：真实 no-motion `POST /api/robot-control/radar/scan-proof/refresh` 返回 `proxy_status=refresh_forwarded`、`remote_http_status=200`、`robot_control_executed=false`；随后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=34`、`radar_overlay_refresh_required=false`。
- 通过：刷新后真实只读 `GET /api/robot-control/live-summary` 返回 `radar_map_points_visible=true`、`live_wysiwyg_missing_surface_ids=["camera"]`、`side_blocker_ids=["camera_wysiwyg","mapping_start"]`、`side_gap_summary_plain="其它缺口：画面所见即所得、传感器就绪后建图；可先做：自由自助移动、键盘连续手控、完整行程执行。"`、`starts_free_roam=false`、`starts_map_runtime=false`、`publishes_cmd_vel=false`。

## 剩余风险

- 本轮只修只读当前所见摘要，不执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 底层 `goal_checklist` 仍保留完整目标验收历史；本轮过滤只作用于 live 当前事实，避免普通用户看到已满足雷达仍被列为当前缺口。
