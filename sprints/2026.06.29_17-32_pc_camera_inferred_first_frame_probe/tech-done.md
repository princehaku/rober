# PC 摄像头共享预览首帧诊断摘要

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：当没有手动首帧探针缓存，但共享 MJPEG/health 已经证明相机源无首帧时，`readback_summary.camera.first_frame_probe_*` 不再保持 `not_loaded`，而是只读推导为 `source_first_frame_failed`、`read_ok=false`、`visible_content_proven=false`，并复用格式尝试摘要。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC 首屏遇到推导出的 `source_first_frame_failed` 时，显示“共享预览已经确认不是页面独占；UVC 没有输出首帧”，避免暴露内部 failure token。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补充 summary 推导字段和普通首屏文案断言。
- `pc-tools/README.md`：记录新的只读 camera summary 合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`，`166 passed`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`，`217 passed`。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build 成功，仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：PC Node 重启到 `0.0.0.0:7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`。
- 通过：live 只读 summary 返回 `camera.status=source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_usage_owner_count=0`、`first_frame_probe_status=source_first_frame_failed`、`first_frame_probe_read_ok=false`、`first_frame_probe_visible_content_proven=false`、`first_frame_probe_fallback_attempts_summary=MJPG@640x480@30 无首帧；MJPG@480x320@30 无首帧；YUYV@320x240@25 无首帧`。
- 通过：live 只读 summary 同时确认 `shared_preview_contract=single_shared_capture_for_multiple_clients`，谁进入 PC 页面都接入同一条共享预览上游，不是页面独占。
- 通过：live 只读 summary 显示 `radar.status=radar_stopped`、地图当前雷达点 `0`、旧来源点 `81` 仅作诊断；显示 `nav2.status=goal_succeeded_wheel_feedback_not_proven`，路线可重跑复验且相机/雷达不是发车前置；显示 `free_roam.status=start_ready`，自由移动可启动。

## 剩余风险

- 本轮不触发 manual/keyboard/Nav2/free-roam/delivery/stop 或 `/cmd_vel`，因此不证明小车真实移动。
- 现场摄像头仍未出首帧，当前证据指向 USB、摄像头输入、格式或供电问题；软件侧已明确不是页面独占。
- 自动驾驶真实移动仍需 CEO 在现场确认安全后重跑 Nav2/自由移动复验；当前只读证据显示可重跑，但未发送运动命令。
