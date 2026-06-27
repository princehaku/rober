# PC 摄像头共享当前事实

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“当前事实”的画面行新增共享预览摘要：页面观看数、共享流是否连接、是否独占。
  - 摄像头首帧失败时继续用普通用户文案说明原因，并带上已选设备名，例如 `USB Composite Device: DV20 USB`。
  - 该逻辑只读取 `readback_summary.camera`，不会打开相机、发起 WebRTC、发送手控、Nav2、delivery、free-roam 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 live 形态回归断言，锁定“0 个页面观看、共享流未连接、不是独占、DV20 无首帧/多方式无帧”显示在当前事实里。
- `docs/product/pc_tools_workstation.md`
  - 同步记录共享当前事实的产品口径和只读安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "camera|当前事实|共享画面"`
  - `Test Files 1 passed`
  - `Tests 25 passed | 136 skipped`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite 仍提示单 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮功能。
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed`
  - `Tests 282 passed`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`
- 通过：`curl -fsS http://127.0.0.1:7001/api/health`
  - 返回 `schema=trashbot.pc_tools_workstation.health.v1`、`mode=pc_only_readonly_workstation`。
- live 只读确认：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - camera 为 `source_first_frame_failed`，`shared_preview_client_count=0`，`shared_preview_upstream_active=false`，
    `shared_preview_exclusive_camera_claim=false`，`selected_name=USB Composite Device: DV20 USB`，
    `source_usage_status=not_in_use`，`source_usage_owner_count=0`。

## 剩余风险

- 本轮只修 PC 普通首屏的 WYSIWYG 解释，不修复真实 `/dev/video1` 无首帧。
- 真实摄像头画面恢复仍要继续定位 UVC/输入/USB/供电；真实自动驾驶运动仍需要现场安全确认后做运动验证。
- 本轮未执行真实手控、Nav2 或 free-roam 运动命令，避免在没有现场安全确认时发车。
