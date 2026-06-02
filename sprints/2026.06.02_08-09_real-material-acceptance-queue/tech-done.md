# Real Material Acceptance Queue Tech Done

## Sprint Type

`sprint_type: micro`

单 owner：`full-stack-software-engineer`

目标：在 PC workstation 中新增 O5/O6/O7 真实材料验收/下一步动作摘要能力，只消费已有 artifact/health/smoke JSON，不执行 probe、不联网、不读取硬件、不发送机器人控制。

## 实际改动

- 新增 `GET /api/real-material/acceptance`，schema 为 `trashbot.pc_tools_workstation.real_material_acceptance.v1`。
- 新增 `pc-tools/workstation/src/server/realMaterialAcceptance.ts`，只读聚合：
  - O5/O6：`GET /api/o5-o6/external-probe-artifact` 的脱敏 artifact 摘要。
  - O7：`ROBER_O7_BROWSER_SMOKE_RESULT_JSON` 或 `.workstation-runtime/o7-browser-playback-smoke.json`。
- 新增共享合同类型 `RealMaterialAcceptanceResponse` / `RealMaterialAcceptanceItem`。
- 新增 Vue 组件 `RealMaterialAcceptancePanel.vue`，在 O7 Console 首屏展示：
  - `accepted / needs_long_run / not_observed / blocked` summary。
  - O5 TLS/external probe、O6 archive external probe、O7 browser long stability 三条 queue item。
  - 每条材料的 blocking reason、next action、proof boundary、artifact status、artifact freshness 和人工采集 runbook 摘要。
- 前端 client snapshot 新增 `getRealMaterialAcceptance()`，由 `App.vue` 统一加载。
- 补充 `catalog.test.ts` 与 `App.test.ts`，覆盖 queue 的 artifact-only 消费、缺材料 fail-closed、UI 展示和固定安全字段。
- 更新产品文档 `docs/product/pc_tools_workstation.md`。
- 新增接口文档 `docs/interfaces/real_material_acceptance_queue.md`。

## 接口与安全边界

- 新接口：`GET /api/real-material/acceptance`
- 固定 fail-closed：
  - `safe_to_control=false`
  - `sends_commands=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
- 固定执行策略：
  - `reads_existing_artifacts_only=true`
  - `network_probe_executed=false`
  - `hardware_read_executed=false`
  - `post_executed=false`
  - `robots_path_accessed=false`
  - `webrtc_session_created=false`
- 不访问 `/robots/*`，不创建 WebRTC session，不发送 `/offer`，不触发 O5/O6 external probe。

## 验证结果

- `cd pc-tools/workstation && npm run test`
  - 通过：`Test Files 2 passed (2)`，`Tests 57 passed (57)`。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 输出 `35 modules transformed`。
- `cd pc-tools/workstation && npm run lint`
  - 通过：`eslint .` 退出码 0。
- scoped `git diff --check`
  - 通过：本轮改动文件无 whitespace error。

## 剩余风险

- 该队列只消费已有 JSON artifact，不采集真实材料；O5/O6/O7 的真实公网 HTTPS、真实 4G/SIM、production DB/queue、真实 180s/3-5min browser artifact 仍需 operator 另行执行并落盘。
- 即使队列 item 进入 `accepted`，也只代表该类 artifact 满足当前合同消费条件，不代表 OKR 自动提升或真实机器人控制能力完成。
- O1 远端 SSH / WAVE ROVER / LiDAR / HIL blocker 本轮未触碰，符合本轮禁止继续消费 O1 SSH blocker 的边界。
