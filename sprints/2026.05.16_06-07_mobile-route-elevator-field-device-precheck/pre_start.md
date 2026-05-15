# Sprint 2026.05.16_06-07 Mobile Route Elevator Field Device Precheck - Pre Start

sprint_type: epic

## 1. 启动原因

本轮按当前 `OKR.md` 4.1 重排。Objective 5 数值最低，约 66%，但剩余推进需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部材料。本机只有 Docker，不能继续堆本地 O5 metadata，也不能把 mobile/browser、handoff summary、diagnostics metadata 写成 Objective 5 external proof。

当前最高可行动作是 Objective 4 的真实设备验收入口：在真实手机、真实 PWA prompt/user choice、真实 route/elevator field pass 或现场送达开始前，把 current `mobile/web` 入口、route/elevator handoff summary、真实设备/PWA 观察项、现场材料清单组合成一个 phone-safe precheck/export/intake 包。本轮抓手命名为 `mobile_route_elevator_field_device_precheck`。

该 precheck 也只读支撑 Objective 2 / Objective 3 的受控现场材料准备：它帮助现场前确认同一 `evidence_ref` 下需要采集哪些材料，但不能开启 Start、Confirm Dropoff、Cancel，也不能声明真实手机、真实现场、HIL、dropoff/cancel completion、delivery success 或 O5 external proof。

## 2. 背景证据

- `OKR.md` 4.1：Objective 5 约 66%，是当前数值最低 Objective；缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。本机只有 Docker，继续做本地 O5 metadata 不应推动 O5。
- 最近 commit `4254bc9 Add mobile route elevator handoff browser proof`：本地 Chromium-family proof 已覆盖 route/elevator handoff panel，但这只是 current `mobile/web` PWA 的本地浏览器 proof，不证明真实手机、真实 PWA prompt/user choice、真实 route/elevator field pass、dropoff/cancel completion 或 delivery success。
- 前一轮 commit `1ddcf81 Add route elevator field session handoff`：把 PC console、route completion signal、elevator reconciliation、Robot diagnostics、mobile/web summary 连成同一 `evidence_ref` 的 handoff，但仍需真实现场材料回填。
- 最新 `sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof/final.md` 建议：若无 O5 外部材料，下一轮优先推进 Objective 4 的真实设备验收入口，或 Objective 2/O3 的受控现场材料回填；browser proof 只能作为出发前检查，不得写成真实现场通过。
- `docs/product/mobile_user_flow.md`：mobile/web 已有真实手机验收交接会话、PWA 安装提示证据、route/elevator handoff 等 phone-safe 面板；这些面板默认 fail-closed，并保留 not real / 不证明边界。

## 3. 本轮产品北极星

让现场操作者在真实设备和路线/电梯现场开始前，能用手机安全导出一份可回填的 precheck 包：它清楚列出入口、设备/PWA 观察项、route/elevator 材料清单、same-evidence-ref 要求和 not_proven 边界，让现场采集不靠记忆，也不误触发机器人控制。

## 4. Owner 和边界

- Task A `full-stack-software-engineer`：移动端 first-screen panel、whitelist copy/export、fixture/test/doc。必须保持 Start / Confirm Dropoff / Cancel fail-closed。
- Task B `robot-software-engineer`：diagnostics/remote protocol metadata-only fence 或 docs/interfaces fence，确保 precheck metadata 不进入 command、ACK、control、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery success。
- Task C `autonomy-engineer`：`pc-tools/evidence` helper/gate，生成或校验 route+elevator+device precheck summary，用于现场前检查，但只输出 software proof / not_proven。
- Task D `product-okr-owner`：closeout 后更新 OKR、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`，并保守复盘 Objective 4 与 O2/O3 支撑效果。

## 5. 风险和阻塞

- Objective 5 仍被真实外部材料阻塞：没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 时，本轮不得上调 O5。
- 本轮不证明真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery success、WAVE ROVER、真实串口/UART 或 HIL。
- 若后续实现只生成软件 precheck artifact，也只能记录为 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate` 或 blocked evidence。
