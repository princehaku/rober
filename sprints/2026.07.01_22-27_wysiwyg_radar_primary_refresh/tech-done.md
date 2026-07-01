# WYSIWYG 主刷新优先雷达贴图

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当相机缺口已诊断为 USB/full-speed 等硬件 blocker，且雷达点也未贴当前地图时，`live_wysiwyg_primary_refresh_endpoint` 优先返回 `/api/robot-control/radar/scan-proof/refresh`。
  - `live_wysiwyg_primary_refresh_label` 同步返回“刷新雷达扫描读数”，`objective_audit_items` 的 WYSIWYG 项 `source_card_id` 指向 `radar_map_points`。
  - 缺口列表仍保留 `camera` 和 `radar_map_points`，避免掩盖相机仍需“换高速USB后复测”的真实硬件问题。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 补充相机 full-speed USB blocker + 雷达贴图缺口组合下的主刷新优先级断言。
- `pc-tools/README.md`
  - 追加本轮 summary 合同口径。

## 验证结果

已运行：

```bash
$ cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts
Test Files  3 passed (3)
Tests  425 passed (425)

$ cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 1.51s

$ git diff --check
# 通过，无输出

$ HOST=0.0.0.0 PORT=7001 npm run api
# 重启后 lsof 显示 node 监听 TCP *:7001

$ curl -fsS 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787'
{
  "live_wysiwyg_missing_surface_ids": ["camera", "radar_map_points"],
  "live_wysiwyg_primary_refresh_endpoint": "/api/robot-control/radar/scan-proof/refresh",
  "live_wysiwyg_primary_refresh_label": "刷新雷达扫描读数",
  "camera_hardware_action_required": true,
  "camera_hardware_action_label": "换高速USB后复测",
  "wysiwyg_source_card_id": "radar_map_points"
}

$ curl -fsS -X POST 'http://127.0.0.1:7001/api/robot-control/radar/scan-proof/refresh?...'
{
  "schema": "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
  "status": "loaded_fail_closed_summary",
  "robot_control_executed": false
}

$ curl -fsS 'http://127.0.0.1:7001/api/robot-control/map/preview?...'
{
  "radar_overlay_status": "loaded",
  "radar_overlay_current_point_count": 5,
  "radar_overlay_source_point_count": 6,
  "radar_overlay_needs_refresh": false,
  "radar_overlay_blocks_wysiwyg": false
}

$ curl -fsS 'http://127.0.0.1:7001/api/robot-control/summary?...'
{
  "live_wysiwyg_missing_surface_ids": ["camera"],
  "radar_map_points_visible": true,
  "live_wysiwyg_primary_refresh_endpoint": "/api/robot-control/camera/first-frame/probe",
  "live_wysiwyg_primary_refresh_label": "复测相机首帧"
}
```

说明：`npm run build` 仍输出 Vite chunk size warning，这是当前单包体积提示，不影响本轮 TypeScript 合同、DOM 合同或打包通过。

## 剩余风险

- 本轮只改 PC summary 的 no-motion 主动作优先级，并执行一次 no-motion 雷达 proof/map preview 刷新；未启动相机/雷达 lifecycle，未执行 Nav2，未发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 相机当前仍需要硬件处理；该改动只是避免相机硬件 blocker 把可 no-motion 修复的雷达地图贴图入口压住。
