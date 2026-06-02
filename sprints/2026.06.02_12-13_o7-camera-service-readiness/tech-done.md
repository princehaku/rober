# O7 camera service readiness collector

## sprint_type

micro

## 实际改动

- 新增 `pc-tools/workstation/scripts/o7-camera-service-readiness-collector.mjs`，提供 operator-run 的 O7 camera 服务 readiness collector。
- 在 `pc-tools/workstation/package.json` 新增 `npm run o7:camera-service-readiness`。
- 更新 `pc-tools/workstation/src/server/realMaterialAcceptance.ts`，当 O7 browser artifact 显示 connection refused / remote health unreachable 时，`next_action` 优先提示 readiness collector，再重跑 180s long-stability。
- 更新 `pc-tools/workstation/test/catalog.test.ts`，覆盖 readiness collector dry-run fail-closed 字段，以及 O7 blocked queue 的 readiness-first next action。
- 更新 `docs/interfaces/real_material_acceptance_queue.md` 与 `docs/product/pc_tools_workstation.md`，同步 O7 readiness collector、artifact schema、dry-run 和 runbook 边界。
- 收尾修复 `scripts/o7-camera-service-readiness-collector.mjs` 里未使用的 `CAMERA_PORT` 常量，保持探测逻辑和默认端口行为不变。

## 验证结果

1. `cd pc-tools/workstation && npm run o7:camera-service-readiness -- --dry-run`
   - 退出状态：0。
   - 关键输出：`schema=trashbot.o7.camera_service_readiness.v1`，`status=dry_run`，`artifact_written=false`，`network_probe_executed=false`，`ssh_probe_executed=false`，`post_executed=false`，`webrtc_session_created=false`，`offer_executed=false`，`safe_to_control=false`，`sends_commands=false`，`robot_control_executed=false`。
2. `cd pc-tools/workstation && npm run test -- catalog.test.ts`
   - 退出状态：0。
   - 关键输出：`1` 个 test file / `55` 个 tests passed。
3. `cd pc-tools/workstation && npm run test`
   - 退出状态：0。
   - 关键输出：`2` 个 test files / `61` 个 tests passed。
4. `cd pc-tools/workstation && npm run build`
   - 退出状态：0。
   - 关键输出：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 输出 `35 modules transformed`。
5. `cd pc-tools/workstation && npm run lint`
   - 退出状态：0。
   - 关键输出：`eslint .` 完成，无 lint error。
6. `git diff --check -- pc-tools/workstation/package.json pc-tools/workstation/scripts/o7-camera-service-readiness-collector.mjs pc-tools/workstation/src/server/realMaterialAcceptance.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/interfaces/real_material_acceptance_queue.md docs/product/pc_tools_workstation.md sprints/2026.06.02_12-13_o7-camera-service-readiness/tech-done.md`
   - 退出状态：0。
   - 关键输出：无 whitespace error。
7. `cd pc-tools/workstation && npm run o7:camera-service-readiness`
   - 退出状态：1。
   - 结果分类：真实 readiness blocker，不是 completion pass。
   - artifact：`.workstation-runtime/o7-camera-service-readiness.json`，`artifact_written=true`。
   - 关键字段：`status=blocked`，`dry_run=false`，`network_probe_executed=true`，`ssh_probe_executed=true`，`post_executed=false`，`webrtc_session_created=false`，`offer_executed=false`，`safe_to_control=false`，`sends_commands=false`，`robot_control_executed=false`。
   - HTTP 分类：`http_probe.health.status=unreachable`，`http_probe.health.error_category=http_unreachable`；`http_probe.devices.status=unreachable`，`http_probe.devices.error_category=http_unreachable`。
   - SSH 分类：`ssh_probe.status=reachable`，`ssh_probe.camera_port_listening=false`，`ssh_probe.process_hint_present=true`。
   - readiness 分类：`ready_for_long_stability=false`，`http_health_unreachable=true`，`ssh_unreachable=false`，`port_not_listening=true`，`process_hint_missing=false`，`blocked_reasons=["http_health_unreachable","http_devices_unreachable","port_not_listening"]`。

## 剩余风险

- 真实板端 `192.168.1.11:8088` 当前 HTTP `/health` 与 `/devices` 不可达；SSH `root@192.168.1.11:37878` 当前可达，但 readiness artifact 未观察到 `8088` 监听。该结果是 readiness blocker，不作为长稳态完成证据。
- readiness collector 只证明 HTTP/SSH 服务可观测性，不证明 WebRTC 180s 首帧稳定、真实浏览器长稳态、公网 relay、TURN、鉴权、真实手机体验或机器人控制能力。
- 本轮不更新 `OKR.md`；Product / OKR Owner 只读建议 O7 继续保持约 `96% software collector entry + blocked real-material failure classification`，不因 blocked readiness artifact 上调。

## 本轮时间

- 记录时间：2026-06-02 12:39:19 CST
