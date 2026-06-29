# PC Fail-Closed Summary Alias Stability

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`failClosed()` 构造完整 payload 后，从 `readback_summary` 回填 `camera_summary`、`map_summary`、`radar_summary`、`nav2_summary`、`keyboard_summary` 和 `free_roam_summary`，避免 URL 被拒或连接不可读时顶层字段消失。
- `pc-tools/workstation/test/catalog.test.ts`：补充缺地址与 unsafe URL 场景的 6 个顶层 alias 一致性断言。
- `pc-tools/README.md`：记录 fail-closed 也保留 summary alias 的合同边界。

## 验证结果

- `npm run build`：首次暴露误改的 TypeScript return 类型问题；修复后复跑通过，TypeScript、Vite build、server TypeScript 均通过。
- `npm test -- --run test/catalog.test.ts`：首次在旧代码会话中失败于 fail-closed alias 缺失；修复后复跑通过，`1 passed`，`166 passed`。
- 本机部署：已重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 `node` 监听 `*:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- Live unsafe URL summary：`GET /api/robot-control/summary?baseUrl=https://127.0.0.1:8787?token=secret` 返回 `console_status=blocked`、`blocked_reasons=["baseUrl_protocol_not_allowed"]`，且 `camera/map/radar/nav2/keyboard/free_roam` 6 个顶层 summary alias 均存在。
- Live normal summary：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`，6 个顶层 summary alias 均存在；当前真实状态仍是 `camera=source_first_frame_failed`、`radar=radar_stopped`、`keyboard=start_ready`、`free_roam=start_ready`。

## 剩余风险

- 该改动只保证连接失败/URL 拒绝时字段稳定，不改变真实摄像头、雷达、键盘、自由移动或 Nav2 状态。
- 完整目标仍需要现场安全确认后的真实运动验证，以及摄像头首帧和雷达新鲜贴图处理。
