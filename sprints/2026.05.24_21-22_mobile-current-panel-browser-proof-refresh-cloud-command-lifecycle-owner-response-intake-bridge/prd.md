# PRD - Mobile current-panel browser proof refresh cloud command lifecycle owner-response intake bridge

- sprint_type: epic
- sprint: `2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge`
- product capability: `mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge`
- proof boundary: `software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate`
- latest panel under proof: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`

## 用户价值和产品北极星

产品北极星是普通手机用户只通过手机页面就能判断机器人是否安全可控、为什么不能启动、下一步需要补什么证据。当前真实硬件、真实手机/browser、真实云外部证据和 verified terminal result 均缺失时，手机页必须把 support continuity 信息做清楚，同时保持主操作禁用，避免把本地 Docker proof 误解成真实送达、真实手机验收、HIL 或 O5 external proof。

本轮用户价值：把最新 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge` 面板纳入 current-panel fresh-profile browser proof。support reviewer 和普通手机用户应能在本地浏览器门禁里看到同一个 bridge capability、同一个 `software_proof` boundary、同一个 PR #5 thread `PRRT_kwDOSWB9286CJ3tX` / `hardware_material_pending` 背景状态、同一组 false-state flags 和安全 copy。

## OKR 映射

| Objective | 本轮关系 | 进度口径 |
| --- | --- | --- |
| Objective 4：手机用户体验与低成本量产边界 | 本轮直接刷新 `mobile/web` current-panel browser proof，覆盖最新 cloud command lifecycle owner-response intake bridge 面板。 | 保持约 99%，因为这只是 local software proof / browser-gate refresh，不是 true phone/browser proof。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 当前最低约 68%，但本轮不直接推进新的 O5 wrapper。 | 保持约 68%，因为仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof、verified terminal result。 |
| Objective 1：硬件协议可信底盘 | PR #5 `hardware_material_pending` thread 是背景证据，不在本轮解决。 | 保持约 81%，因为 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，且没有真实 LiDAR/ToF、WAVE ROVER/UART 或 HIL。 |

## KR 拆解

| KR | Owner | 需要做什么 | 验收口径 |
| --- | --- | --- | --- |
| KR-A Current-panel browser gate refresh | `full-stack-software-engineer` | 在 browser acceptance gate、mobile focused tests、必要 fixture/docs 中加入 `mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge` capability。 | fresh-profile gate 覆盖 latest panel `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`，显示 `software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate`，console clean，主操作 disabled。 |
| KR-B Robot/API safe alias consultation | `robot-software-engineer` | 只读确认现有 cloud command lifecycle owner-response intake bridge safe summary 是否足够支撑 mobile panel；必要时只更新接口/产品文档。 | 不新增 raw diagnostic，不新增 robot command side effect，不暴露 `/cmd_vel`、串口、WAVE ROVER/UART、ACK/cursor mutation、GitHub mutation、replay/resubmit 或 material upload。 |
| KR-C Product closeout | `product-okr-owner` | implementation validation 后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。 | 明确 no OKR percentage lift，Objective 5 仍约 68%，并保留 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。 |

## 本轮核心抓手

本轮核心抓手是 O4 `mobile/web` current-panel browser proof refresh，而不是继续推进 O5 local-only wrapper。最新 O5 bridge 已经存在；本轮只证明该 bridge 在手机当前面板中以本地 fresh-profile browser proof 的方式可见、可解释、fail closed，并且不会开启机器人控制或支持误读。

## 范围边界

In scope:

- 新增或扩展 browser gate capability：`mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge`。
- 使用 boundary：`software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate`。
- 覆盖 latest panel：`cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`。
- 保留 `PRRT_kwDOSWB9286CJ3tX`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 保持本地 browser-gate / local Chromium-family software proof 口径。

Out of scope:

- 不新增 O5 local-only wrapper，不把 local-only wrapper 当 OKR lift。
- 不改硬件配置，不声明真实 WAVE ROVER/UART、LiDAR/ToF、HIL 或实机 powered bench。
- 不声明 true phone/browser proof、真实 iPhone/Android device behavior、production PWA install proof。
- 不声明 O5 external proof、public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、verified terminal result。
- 不声明 route/elevator field pass、Nav2/fixed-route runtime pass 或 delivery success。

## 优先级和验收口径

P0:

- Full-Stack gate 必须能在 fresh-profile browser proof 中覆盖 cloud command lifecycle owner-response intake bridge panel。
- 页面和 proof artifact 必须显示 `software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate`。
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 必须保持。

P1:

- Robot consultation 必须确认现有 safe summary 足够，或只补接口/产品文档说明。
- Product closeout 必须在 implementation validation 后同步 sprint final、OKR snapshot 和 okr_progress_log。

P2:

- 如果 fresh-profile gate 已支持 `--capability` / `--evidence-boundary` override，应优先复用，不新增重复 proof script。

## 责任 Engineer

- `full-stack-software-engineer`：主责实现、fixture、focused unit/browser gate 验证。
- `robot-software-engineer`：read-only consultation，确认 Robot/API safe alias 和接口 side effect 边界。
- `product-okr-owner`：planning docs 和 implementation 后 closeout 文档、OKR/progress log。

## 风险、阻塞和证据链

- 最新 final 已明确 `do not add another local-only wrapper as OKR lift`；本轮选择 O4 fallback 是为了 current-panel browser proof refresh，不是 O5 进度提升。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；PR #7 open / review threads empty 不能解除该缺口。
- O5 真实进展仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof、verified terminal result；本轮 no OKR percentage lift。
- 本轮证据链只允许写成 local software proof / browser-gate refresh；fresh-profile screenshot/JSON 也不等于真实手机/browser proof。
