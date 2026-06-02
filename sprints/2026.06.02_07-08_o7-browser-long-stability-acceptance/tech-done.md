# O7 Browser Long Stability Acceptance Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts` 新增 `O7LongStabilityAcceptanceSummary`，并把 `browser_smoke.long_stability_acceptance` 纳入 O7 local WebRTC camera contract。
- `pc-tools/workstation/src/server/o7LocalWebrtcCamera.ts` 在显式 browser smoke artifact 消费层派生 3-5 分钟长稳态验收摘要；默认要求 `required_window_ms=180000`，30s artifact 只输出 `needs_long_run`，健康 180s artifact 输出 `accepted`，关键条件失败输出 `failed`，无观察输出 `not_observed`。
- `pc-tools/workstation/src/components/O7LocalCameraSmokePanel.vue` 新增 `3-5min acceptance` 展示行，operator 可直接看到当前 artifact 是否足够做 O7 长稳态证据。
- `pc-tools/workstation/test/catalog.test.ts` 覆盖 30s `needs_long_run` 与 180s `accepted` 两类机器可读判定。
- `pc-tools/workstation/test/catalog.test.ts` 补充 no-artifact 场景的临时缺失 smoke path，避免本机 `.workstation-runtime/o7-browser-playback-smoke.json` 残留把 fail-closed 用例污染成 30s `needs_long_run`。
- `pc-tools/workstation/test/App.test.ts` 覆盖 UI 对 `3-5min acceptance`、`needs_long_run` 和 `required_ms=180000` 的展示。
- `docs/interfaces/o7_local_webrtc_camera_smoke.md` 与 `docs/product/pc_tools_workstation.md` 同步记录字段语义和产品边界。

## 验证结果

2026-06-02 07:48 已运行指定验收命令：

1. `cd pc-tools/workstation && npm run test`
   - exit 0，通过。
   - 关键输出：`Test Files  2 passed (2)` / `Tests  55 passed (55)` / `Duration  14.64s`。
2. `cd pc-tools/workstation && npm run build`
   - exit 0，通过。
   - 关键输出：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`、`33 modules transformed`、`built in 2.98s`。
3. `cd pc-tools/workstation && npm run lint`
   - exit 0，通过。
   - 关键输出：`eslint .`，无报错输出。
4. `git diff --check -- pc-tools/workstation/src/server/o7LocalWebrtcCamera.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7LocalCameraSmokePanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_local_webrtc_camera_smoke.md docs/product/pc_tools_workstation.md sprints/2026.06.02_07-08_o7-browser-long-stability-acceptance/tech-done.md`
   - exit 0，通过。
   - 关键输出：无 whitespace error 输出。

## 剩余风险

- 本轮只消费已有显式 browser smoke JSON，不生成新的 3-5 分钟真实 artifact；O7 真实长稳态仍需 operator 运行 `ROBER_O7_BROWSER_SMOKE_STABILITY_MS=180000 npm run o7:browser-smoke` 后再由 PC API/UI 摘要消费。
- `safe_to_control=false`、`offer_executed=false`、`webrtc_session_created=false`、`robot_control_executed=false` 保持不变；本轮不证明云 relay、公网 TURN、鉴权、真实用户手机/browser、ROS2/Nav2 或机器人控制。
- 本轮不修改 `OKR.md`；是否小幅提进度应等真实 3-5 分钟 artifact 或至少合同守卫验证通过后由 OKR owner 决定。

## O7 最低优先级说明

本轮是 O7 指定 micro sprint，不针对当前最低 O1。原因是 CEO 明确要求避免 O7 继续消费已关闭的 first-frame blocker，并补齐 30s 与 3-5 分钟证据之间的产品入口安全边界。
