# O7 Browser Playback Smoke Micro Sprint

## sprint_type

micro

## 实际改动

- 新增 `pc-tools/workstation/scripts/o7-browser-playback-smoke.mjs`：显式 same-LAN browser playback smoke，默认打开 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL` 或 `http://192.168.1.11:8088/`，点击页面 `Start WebRTC video`，收集首帧、`videoWidth/videoHeight`、首帧耗时、ICE/connection/signaling 状态、console/page errors，并输出 `trashbot.o7.local_webrtc_browser_playback_smoke.v1` JSON。
- 更新 `pc-tools/workstation/src/server/o7LocalWebrtcCamera.ts` / `src/shared/contracts.ts` / `src/components/O7LocalCameraSmokePanel.vue`：PC API/UI 只读 `.workstation-runtime/o7-browser-playback-smoke.json` 或 `ROBER_O7_BROWSER_SMOKE_RESULT_JSON` 指向文件，展示 browser smoke 是否执行、首帧是否证明、关键指标和 blocked reason；API 自身仍只 GET `/health` + `/devices`，不 POST `/offer`。
- 更新 `docs/interfaces/o7_local_webrtc_camera_smoke.md` 和 `docs/product/pc_tools_workstation.md`：补充 same-LAN browser smoke 命令、JSON 字段、安全边界和 fail-closed 降级语义。

## 验证结果

- `cd pc-tools/workstation && npm run o7:browser-smoke`：通过并输出 `status=degraded` JSON；根因是 `playwright_dependency_missing_use_npx_p_playwright_or_install_browser_runtime`，因此 `first_frame_received=false`、`browser_available=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`。结果写入 `.workstation-runtime/o7-browser-playback-smoke.json`，可被 PC API/UI 只读消费。
- `cd pc-tools/workstation && npm run test`：通过，`2 passed (2)`，`45 passed (45)`。
- `cd pc-tools/workstation && npm run build`：通过，Vite 构建 `33 modules transformed`，server TypeScript 构建通过。
- `cd pc-tools/workstation && npm run lint`：通过，无输出。
- `git diff --check -- pc-tools/workstation docs/interfaces/o7_local_webrtc_camera_smoke.md docs/product/pc_tools_workstation.md sprints/2026.06.01_04-05_o7-browser-playback-smoke/tech-done.md`：通过，无输出。

## OKR 口径

本轮推进了 O7 的真实浏览器播放验收入口和 PC 端证据消费，但当前环境缺 Playwright/Chromium，未拿到 `first_frame_received=true` 的真实浏览器证据。因此 O7 不建议因本轮从约 92% 上调；当前有效进展是把下一步真实同 WiFi 浏览器验收变成一条可重复命令和可展示证据，而不是完成真实浏览器播放验收。

## 剩余风险

- 当前工作站环境未确认有 Playwright/Chromium。若浏览器依赖缺失，本轮只能留下 `degraded` JSON，不能证明真实同 WiFi 浏览器首帧。
- 未运行远端 `192.168.1.11:8088` 长时间播放或稳定性测试；本 sprint 只覆盖显式首帧 smoke 入口和 PC 只读证据展示。
- O7 进度是否从约 92% 上调需要 Product/OKR owner 根据真实浏览器首帧 JSON 决定；只有依赖缺失的 degraded 输出不建议上调。
