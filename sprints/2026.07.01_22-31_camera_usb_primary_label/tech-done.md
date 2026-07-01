# 相机硬件 blocker 主动作明确化

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当当前所见只剩相机缺口且 `camera_hardware_action_required=true` 时，`live_wysiwyg_primary_refresh_label` 改为“换高速USB后复测相机首帧”。
  - `live_wysiwyg_primary_refresh_endpoint` 保持 `/api/robot-control/camera/first-frame/probe`，只读复测入口不变。
  - WYSIWYG objective 的下一步同步显示“换高速USB后复测相机首帧”，避免普通用户误以为只需要反复点复测。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 新增地图/雷达已 WYSIWYG、相机 USB full-speed blocker 的 summary 合同测试。
- `pc-tools/README.md`
  - 追加 2026-07-01 22:31 CST 当前口径。

## 验证结果

已运行：

```bash
$ cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts
Test Files  3 passed (3)
Tests  426 passed (426)

$ cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 1.54s

$ git diff --check
# 通过，无输出

$ HOST=0.0.0.0 PORT=7001 npm run api
# 重启后 lsof 显示 node 监听 TCP *:7001

$ curl -fsS 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787'
{
  "live_wysiwyg_missing_surface_ids": ["camera"],
  "live_wysiwyg_primary_refresh_endpoint": "/api/robot-control/camera/first-frame/probe",
  "live_wysiwyg_primary_refresh_label": "换高速USB后复测相机首帧",
  "camera_hardware_action_required": true,
  "camera_hardware_action_label": "换高速USB后复测",
  "camera_usb_speed": "12M",
  "radar_map_points_visible": true,
  "map_current_visible": true,
  "wysiwyg_next_action_plain": "下一步：换高速USB后复测相机首帧。",
  "wysiwyg_source_card_id": "camera_preview",
  "sends_motion_when_clicked": false
}
```

说明：`npm run build` 仍输出 Vite chunk size warning，这是当前单包体积提示，不影响本轮 TypeScript 合同、DOM 合同或打包通过。

## 剩余风险

- 本轮只改 PC summary 的只读文案和验收合同，不启动相机/雷达 lifecycle，不执行 Nav2，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 相机仍需要现场换高速 USB 口/线或带供电 Hub 后复测；软件侧不能替代物理链路修复。
