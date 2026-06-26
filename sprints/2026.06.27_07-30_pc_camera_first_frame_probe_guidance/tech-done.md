# PC 摄像头首帧只读检查提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏实时画面卡在相机源首帧失败、且还没有跑过只读首帧检查时，新增 `只读检查` 下一步提示。
  - 提示明确说明点击 `检查画面（只读）` 会确认上位机能否读到样张，且不会发车。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 live 形状：`source_usage_owner_count=0`、`capture_read_returned_false`、共享 MJPEG 上游失败时，首屏仍显示“不是独占”，并补充未跑首帧检查的只读提示。
  - 继续锁定该状态不会调用 manual、free-roam、Nav2、delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录摄像头首帧失败但 `first_frame_probe_status=not_loaded` 时的普通首屏动作边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 153 passed (153)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 保留既有 chunk size warning，本轮无新增构建失败。
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node` PID `55861` 监听 `TCP *:7001`。
  - `curl http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`、`safe_to_control=false`、`pc_only=true`。
  - `curl http://127.0.0.1:7001/api/robot-control/summary` 返回 live 事实：摄像头 `source_first_frame_failed`、`source_usage_owner_count=0`、`source_failure_reason=capture_read_returned_false`、`first_frame_probe_status=not_loaded`、`shared_preview_exclusive_camera_claim=false`。

## 剩余风险

- 本轮只补普通首屏的摄像头只读诊断下一步，不修复 `/dev/video1` 当前首帧读取失败的硬件/驱动根因。
- live 当前摄像头仍显示不是独占但无首帧；需要后续继续查 USB、摄像头输入、格式或供电。
