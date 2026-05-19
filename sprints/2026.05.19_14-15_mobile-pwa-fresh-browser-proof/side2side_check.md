# Sprint 2026.05.19_14-15 Mobile PWA Fresh Browser Proof - Side2Side Check

## sprint_type: epic

Run time: 2026-05-19 14:29 Asia/Shanghai。

## 1. PRD 验收对照

| PRD 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Fresh profile browser proof 能稳定运行，输出 JSON/screenshot/summary | 通过 | `mobile_pwa_fresh_browser_proof_390x844.json/png`、`mobile_pwa_fresh_browser_proof_768x900.json/png`、`mobile_pwa_fresh_browser_proof_summary.json` 已生成。 |
| Console/runtime error 为 0 | 通过 | 两个 viewport 均 `console_zero_status=passed`、`console_error_count=0`，summary `ok=true`。 |
| Start Delivery、Confirm Dropoff、Cancel fail-closed | 通过 | Summary 保持 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`；Robot review 未发现控制面扩大。 |
| Dynamic control paths no-store/bypass cache | 通过 | Robot review 确认 `/api/*`、`/robots/*`、commands、ACK、diagnostics、collect/dropoff/cancel 等动态控制面不被 service-worker 缓存、排队或重放。 |
| Summary 包含 viewport、marker、boundary、not_proven 和 artifact paths | 通过 | Fresh proof summary 固定 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`，并保留 `not_proven`。 |
| `docs/product/mobile_user_flow.md` 同步更新 | 通过 | Full-Stack 已记录 fresh browser proof gate 的命令入口、artifact 名称、console-zero 和证据边界。 |

## 2. 用户价值复核

本轮解决的是 Objective 4 的本地验收噪声：上一轮旧 PWA cache / 旧 console log 让 Browser QA 不能稳定区分当前 shell 和历史缓存壳。本轮 fresh Chromium profile proof 让现场 owner 能在真实手机验收前先拿到干净的软件预检结果。

这提升的是“本地软件护栏可复核性”，不是普通用户真实手机验收完成度。因此 Objective 4 可以记录 local fresh browser proof，但仍保持约 99%，不声称真实 iPhone/Android、production app 或真实 PWA prompt/user choice 通过。

## 3. OKR 边界复核

- Objective 5：本轮没有 HTTPS/TLS 公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover，保持约 68%。
- Objective 1：本轮没有 WAVE ROVER/UART/HIL、真实串口日志、`feedback_T1001.log`、operator HIL report 或 PR #5 真实 2D LiDAR / ToF 材料，保持约 81%。
- Objective 2 / Objective 3：本轮没有 PR #4 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、dropoff/cancel completion 或 delivery success，保持约 99%。
- Objective 4：本轮只记录 `mobile_pwa_fresh_browser_proof` 本地软件证明，保持约 99%。

## 4. 验收结论

本轮 PRD P0/P1 均已满足。证据边界必须写作 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

未完成事项全部是外部/现场材料：真实手机/browser、production app、真实 PWA prompt/user choice、O5 external proof、WAVE ROVER/UART/HIL、PR #4 field pass、PR #5 real materials 和真实 delivery success。
