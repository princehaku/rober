# Sprint 2026.05.19_13-14 Mobile PWA Cache Recovery - Side2Side Check

## sprint_type: epic

Run time: 2026-05-19 14:20 Asia/Shanghai。

## 1. 用户价值和产品北极星核对

本轮产品北极星是让普通手机用户后续能稳定看到当前 `mobile/web` shell，而不是被旧 service-worker/offline shell 缓存卡住。实际交付符合该目标：Full-Stack 提供 `mobile_pwa_cache_recovery`，本地 Browser QA fresh tab DOM proof 显示 `hasCurrentShell=true`、`hasOfflineShell=false`，且 Start Delivery、Confirm Dropoff、Cancel 均 disabled。

本轮仍不是业务闭环完成：没有真实手机、真实 PWA prompt/user choice、production app、真实 route/elevator field pass、真实 delivery success、Objective 5 external proof 或 Objective 1 HIL。

## 2. OKR 映射核对

| Objective | 收口判断 |
| --- | --- |
| Objective 5 | 保持约 68%。本轮没有真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。 |
| Objective 1 | 保持约 81%。本轮没有 WAVE ROVER/UART/HIL、`feedback_T1001`、`odom/imu/battery` 或 PR #5 真实 2D LiDAR / ToF materials。 |
| Objective 4 | 保持约 99%。本轮只记录本地 Browser QA cache recovery software-proof，帮助后续真实 iPhone/Android / PWA prompt / production app 验收前减少 stale shell 噪声。 |
| Objective 2/3 | 保持约 99%。本轮不证明 PR #4 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion 或 delivery_success。 |

## 3. Side-by-side 验收

| PRD / tech-plan 口径 | 实际证据 |
| --- | --- |
| 本地 PWA 不再长期停在旧 offline shell。 | Browser validation fresh tab DOM proof：`hasCurrentShell=true`、`hasOfflineShell=false`、`marker=mobile_pwa_cache_recovery`、`boundary=software_proof_docker_mobile_pwa_cache_recovery_gate`。 |
| Offline shell recovery 不启用控制动作。 | Full-Stack tests 覆盖 offline recovery fail-closed；Browser DOM proof 显示 Start/Confirm/Cancel disabled。 |
| Service-worker cleanup 不误删不相关 cache。 | Robot 建议后 Full-Stack 修正 activate cleanup，仅删除旧 `rober-mobile-shell-*` cache，保留当前 cache 与同源其他 cache。 |
| Robot 控制面不扩大。 | Robot post-diff read-only review：`/api/*`、`/robots/*`、commands、ACK、diagnostics、non-GET 仍 no-store/bypass cache；marker 只用于 static shell cache recovery。 |
| 文档同步。 | `docs/product/mobile_user_flow.md` 已记录 `mobile_pwa_cache_recovery`、`service-worker`、`offline shell` 与 `software_proof` 边界。 |

## 4. 风险、阻塞和证据链

- Browser QA 是本地 in-app browser DOM proof；Chrome headless screenshot/console attempt hung and was terminated without committing artifacts。
- in-app browser dev logs 保留了一条恢复前旧 cached app shell console error；当前 fresh tab DOM 已证明当前 shell 与 fail-closed 状态，但不等于严格 console-zero。
- 仍缺真实 iPhone/Android、真实 PWA prompt/user choice、production app、真实 phone/browser acceptance、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、WAVE ROVER/UART/HIL、PR #4 route/elevator field pass、PR #5 真实 hardware materials、dropoff/cancel completion 和 delivery_success。
- 证据边界必须继续写作：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
