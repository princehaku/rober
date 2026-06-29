# PC Camera Health Device Fallback

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：在 camera summary 中保留原 `devices_status`，新增 `devices_effective_status`、`devices_endpoint_count`、`devices_health_candidate_count` 和 `devices_plain_hint`。当 `/api/camera/devices` 返回空列表但 `camera_health.source_summary.candidates` 已读到候选时，summary 明确按 health 候选继续诊断。
- `pc-tools/workstation/src/shared/contracts.ts`：补充新增 camera summary 字段的类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏实时画面卡新增“设备事实”提示，高级诊断同步展示 effective status 和计数。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 live 形态下 devices 空列表、health 候选可用时的 summary 和普通首屏显示。
- `pc-tools/README.md`：同步记录只读 camera health fallback 口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`，166 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`，218 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，client/server TypeScript 与 Vite build 成功；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 `node` 监听 `*:7001`。
- 通过：live summary 确认 `devices_status=loaded`、`devices_effective_status=loaded_from_health_source_summary`、`devices_endpoint_count=0`、`devices_health_candidate_count=3`、`selected_path=/dev/video1`、`selected_name=USB Composite Device: DV20 USB`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_usage_owner_count=0`。

## 剩余风险

- 本轮只修 PC 端只读诊断与显示，不修复 UVC 设备真实无首帧。live 当前根因仍需现场检查 USB、摄像头输入、格式或供电，必要时换 known-good UVC 复测。
- 本轮不启动摄像头独占采集、不重启上车相机服务、不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
