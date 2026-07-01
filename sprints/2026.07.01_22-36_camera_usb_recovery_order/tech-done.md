# 相机 USB 恢复顺序文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将 USB/full-speed 相机 blocker 的恢复长文案改为先提示“换高速USB后复测”，再提示读取共享预览状态。
  - `live_wysiwyg_camera_recovery_next_action_plain` 和建图解锁相机文案同步使用该顺序，避免现场在 USB 12M 已确认时反复点首帧复测。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 更新 full-speed USB 相机诊断断言，锁住“先处理 USB，再复测”的口径。
- `pc-tools/README.md`
  - 追加 2026-07-01 22:36 CST 口径。

## 验证结果

已运行：

```bash
$ cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts
Test Files  3 passed (3)
Tests  426 passed (426)

$ cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 1.50s

$ git diff --check
# 通过，无输出

$ HOST=0.0.0.0 PORT=7001 npm run api
# 重启后 lsof 显示 node 监听 TCP *:7001

$ curl -fsS 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787'
{
  "live_wysiwyg_missing_surface_ids": ["camera"],
  "live_wysiwyg_primary_refresh_label": "换高速USB后复测相机首帧",
  "live_wysiwyg_camera_recovery_next_action_plain": "相机不是页面独占；诊断显示 USB full-speed；先换高速USB后复测，再读取共享预览状态。当前硬件提示：摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测。",
  "mapping_unblock_camera_recovery_next_action_plain": "相机不是页面独占；诊断显示 USB full-speed；先换高速USB后复测，再读取共享预览状态。当前硬件提示：摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测。",
  "camera_usb_speed": "12M",
  "camera_hardware_action_required": true,
  "map_current_visible": true,
  "radar_map_points_visible": true,
  "sends_motion_when_clicked": false
}
```

说明：`npm run build` 仍输出 Vite chunk size warning，这是当前单包体积提示，不影响本轮 TypeScript 合同、DOM 合同或打包通过。

## 剩余风险

- 本轮只改 PC summary 的只读文案，不启动相机/雷达 lifecycle，不执行 Nav2，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 相机硬件链路仍需现场换高速 USB 口/线或带供电 Hub 后复测。
