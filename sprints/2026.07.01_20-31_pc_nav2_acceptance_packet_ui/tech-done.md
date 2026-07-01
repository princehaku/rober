# PC 行程卡消费 Nav2 验收包

## sprint_type: micro

## 实际改动

- `plain-trip-closure-readback` 和 `plain-live-trip-closure-readback` 优先消费 `nav2_route_acceptance_packet`，旧 `live_motion_runbook` 只作兼容兜底。
- 行程闭环 DOM 新增 packet 来源、启动/停止端点、最小预检、同窗口 wheel raw L/R、样本计数、delivery 端点和 readback no-motion 边界。
- 读回按钮改用 packet 的 `readback_endpoints`，继续保持只读，不执行 Nav2、不发送 manual/keyboard/free-roam/建图、不提交 delivery、不 stop。
- 同步 `docs/product/pc_tools_workstation.md` 和 App 测试，确保普通可见文案仍保持“图上路线、到点、同窗口轮速、送达确认”的简易风格。

- 通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - 首轮失败于测试期望使用“图上路线已显示”，实际普通用户文案为“图上行程已显示”；按现有简易口径修正测试后通过。
  - `Test Files 1 passed (1)`
  - `Tests 233 passed (233)`
- 通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`
  - `Test Files 2 passed (2)`
  - `Tests 190 passed (190)`
- 通过：`npm --prefix pc-tools/workstation run lint`
- 通过：`npm --prefix pc-tools/workstation run build`
  - Vite 仍有既有 chunk size warning，非本轮新增错误。
- 通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Test Files 3 passed (3)`
  - `Tests 423 passed (423)`
- 通过：重启 PC Node 到 `0.0.0.0:7001`，listener PID `52651`。
  - `GET http://127.0.0.1:7001/` 返回 `200`。
  - `GET http://127.0.0.1:7001/map` 返回 `200`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `source_base_url=http://192.168.1.11:8787`，`nav2_route_acceptance_packet.action_id=run_nav2_route`，`ready=true`，`completed=false`，`start_endpoint=/api/robot-control/nav2/goal/execute`，`requires_safety_confirm=true`，`minimal_precheck_safety_only=true`，`readback_sends_motion=false`，`readback_starts_nav2=false`，`readback_submits_delivery=false`，`readback_stops_motion=false`。

## 剩余风险

- 本轮只接 UI/DOM 只读验收包，不执行真实 Nav2 路线、不发底盘命令、不提交 delivery success；真实车动闭环仍需现场安全确认后另行 HIL 验证。
