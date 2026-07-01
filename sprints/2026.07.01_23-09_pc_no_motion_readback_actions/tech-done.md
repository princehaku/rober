# PC 只读复验动作清单

sprint_type: micro

## 实际改动

- `field_acceptance_packet` 新增 `no_motion_readback_actions[]`，每个动作包含普通用户 `label`、固定 `endpoint`、`method`、短说明和所有“不发车”标志。
- `GET /api/robot-control/summary` 顶层新增 `field_acceptance_no_motion_readback_action_*` 与 `field_acceptance_primary_no_motion_readback_action_*` 字段。
- 普通首屏 `plain-field-acceptance-packet` 和 `plain-field-acceptance-remaining-actions` 同步暴露只读动作 labels/endpoints/methods/primary。
- primary 规则：
  - 雷达贴图不是当前图时，优先 `refresh_radar_map_overlay`。
  - 否则当前所见仍有缺口时，优先 `refresh_current_wysiwyg`。
  - 都无缺口时，回到 `readback_all`。
- `pc-tools/README.md` 同步记录该合同和不发车边界。

## 验证结果

- 已通过：`npm test -- robotControlSummary.test.ts App.test.ts`
  - 结果：`Test Files 2 passed (2)`，`Tests 245 passed (245)`。
- 已通过：`npm run build`
  - 结果：TypeScript app/server 和 Vite production build 通过；仅保留既有 chunk size warning。
- 已通过：`git diff --check`
  - 结果：无 whitespace error。
- 已通过：后台重启 Node 工作站并读取真实 `GET /api/robot-control/summary`
  - 监听：`0.0.0.0:7001`，PID `57564`。
  - 小车地址：`http://192.168.1.11:8787`。
  - 结果：`status=needs_wheel_rerun`，`live_wysiwyg_missing_surface_ids=["camera","radar_map_points"]`，`radar_overlay_status=not_current`。
  - 结果：`field_acceptance_no_motion_readback_action_ids=["readback_all","refresh_current_wysiwyg","refresh_radar_map_overlay"]`。
  - 结果：`field_acceptance_no_motion_readback_action_endpoints=["/api/robot-control/summary","/api/robot-control/radar/scan-proof/refresh","/api/robot-control/radar/scan-proof/refresh"]`。
  - 结果：`field_acceptance_no_motion_readback_action_methods=["GET","POST","POST"]`。
  - 结果：primary 为 `refresh_radar_map_overlay` / `POST /api/robot-control/radar/scan-proof/refresh`，`primary_sends_motion=false`。
  - 结果：packet action 全部 `sends_motion=false`，且 `starts_nav2/manual/free_roam/map_runtime/radar_lifecycle=false`。

## 剩余风险

- 这轮只补 PC/API 的只读验收动作合同，不替代现场安全确认，也不主动执行 Nav2、键盘、自由移动或建图。
- 当前真实小车仍需要现场安全确认后执行运动项，且相机 USB/full-speed 缺口仍会阻塞建图首帧。
