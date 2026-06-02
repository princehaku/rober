# 2026.06.02 10-11 O7 Long Stability Collector

## Sprint Type

- `sprint_type: micro`
- Owner: `full-stack-software-engineer`
- Objective: O7 PC 端运营调试平台
- Scope: 把 O7 180s browser 长稳态材料采集从 UI runbook 提示推进为 operator-run 命令入口。

## 实际改动

- 新增 `pc-tools/workstation/scripts/o7-browser-long-stability-collector.mjs`：
  - 提供 `npm run o7:browser-long-stability` 的 Node 入口。
  - 默认委托现有 `scripts/o7-browser-playback-smoke.mjs`，不复制 `/offer` 或浏览器 smoke 逻辑。
  - 将 `ROBER_O7_BROWSER_SMOKE_STABILITY_MS` 的有效值强制提升到 `>=180000`，默认输出到 `.workstation-runtime/o7-browser-playback-smoke.json`。
  - 支持 `--dry-run` 输出 `trashbot.o7.browser_long_stability_collector.v1` 机器可读 JSON，固定 `network_probe_executed=false`、`post_executed=false`、`webrtc_session_created=false`、`artifact_written=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`。
- 更新 `pc-tools/workstation/package.json`，新增 `o7:browser-long-stability` npm script。
- 更新 `pc-tools/workstation/src/server/realMaterialAcceptance.ts`，让 `GET /api/real-material/acceptance` 的 O7 runbook 和 next action 指向新入口，而不是要求 operator 手记原始 browser smoke env。
- 更新 `pc-tools/workstation/test/catalog.test.ts` 和 `pc-tools/workstation/test/App.test.ts`：
  - 覆盖 O7 runbook 新命令文案。
  - 覆盖 collector dry-run 不联网、不 POST、不建 WebRTC、不写 artifact 的 fail-closed 计划 JSON。
  - 覆盖低于 180000ms 的窗口会被提升到 180000ms，以及不安全 URL / 非整数窗口会被拒绝。
- 更新 `docs/interfaces/real_material_acceptance_queue.md` 与 `docs/product/pc_tools_workstation.md`，同步 API runbook、collector dry-run 和证明边界。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`，把 O7 口径从 `software guardrail` 调整为 `software collector entry`；由于本轮只验证 dry-run 和入口，不新增真实 180s/3-5min artifact，进度仍保持约 96%。

## 用户旅程变化和触点收益

- Operator 现在可以直接运行 `cd pc-tools/workstation && npm run o7:browser-long-stability` 采集 O7 180s+ browser 长稳态材料，不再需要记住原始 smoke 脚本和 `ROBER_O7_BROWSER_SMOKE_STABILITY_MS=180000` 的组合。
- 无相机或本地只做护栏验证时，可运行 `npm run o7:browser-long-stability -- --dry-run`，拿到可被自动化读取的 fail-closed JSON，确认命令入口、默认输出和安全 flags。
- `GET /api/real-material/acceptance` 继续只读消费 artifact，不自动执行采集；UI 展示的是 operator-run 入口和材料缺口，不冒充真实 180s 浏览器材料已经存在。

## 接口影响

- 新增 npm script：`pc-tools/workstation` 下的 `npm run o7:browser-long-stability`。
- 新增 collector dry-run schema：`trashbot.o7.browser_long_stability_collector.v1`。
- `GET /api/real-material/acceptance` schema 不变，O7 item 的 `collection_runbook.suggested_commands[]`、`required_env[]`、`failure_handling[]` 和 `next_action` 文案更新为新 collector 入口。
- ROS2 / robot / hardware 接口无变更；本轮未修改 O1 代码，未 SSH `192.168.1.11:37878`，未执行真实 WebRTC 180s 采集。

## 验证结果

- `cd pc-tools/workstation && npm run o7:browser-long-stability -- --dry-run`
  - 通过；输出 `status=dry_run`，`stability_ms=180000`，`artifact_written=false`，`network_probe_executed=false`，`post_executed=false`，`webrtc_session_created=false`，`safe_to_control=false`。
- `cd pc-tools/workstation && npm run test`
  - 通过；Vitest 全量测试通过。
- `cd pc-tools/workstation && npm run build`
  - 通过；TypeScript / Vite / server build 通过。
- `cd pc-tools/workstation && npm run lint`
  - 通过；ESLint 无报错。
- `git diff --check -- <本轮触碰文件>`
  - 通过；无 whitespace error。

## 前后端 / ROS2 联调结果

- 前端：`App.test.ts` fixture 已同步 O7 real-material queue 新 runbook 文案；UI 仍只展示后端返回的 runbook，不在 Vue 侧二次推断材料状态。
- 后端：`realMaterialAcceptance.ts` 的 O7 runbook 指向新 collector，execution policy 仍固定只读，不执行 probe。
- ROS2 / robot：本轮没有触碰 ROS2 契约和硬件控制链路；没有真实 180s WebRTC session、没有 `/offer`、没有机器人控制。

## 剩余风险

- `--dry-run` 只能证明入口和 fail-closed 参数规划，不能作为 O7 真实 180s/3-5min browser artifact。
- 真实 O7 长稳态仍需要 operator 在同 LAN camera 可达时运行 collector，并由 `.workstation-runtime/o7-browser-playback-smoke.json` 的 `stability_summary.observation_window_ms >= 180000`、连接/ICE/video/cleanup 条件共同验收。
- 弱网、TURN、公网云 relay、鉴权、真实用户浏览器/手机体验、ASR/TTS、手控/Nav2、真实 robot ACK 和完整上车任务闭环仍为 `not_proven`。
- O1 SSH / `T=1001` blocker 本轮未消费，仍需 CEO/现场恢复网络后另行处理。
