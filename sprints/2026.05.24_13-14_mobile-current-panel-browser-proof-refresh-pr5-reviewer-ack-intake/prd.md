# PRD - Mobile current-panel browser proof refresh PR5 reviewer ACK intake

- sprint_type: epic
- sprint: `2026.05.24_13-14_mobile-current-panel-browser-proof-refresh-pr5-reviewer-ack-intake`
- product capability: `mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake`
- proof boundary: `software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate`

## 用户价值和产品北极星

产品北极星是普通手机用户只通过手机页面就能判断机器人是否安全可控、为什么不能启动、下一步需要补什么证据。当前真实硬件和 O5 external proof 均缺失时，手机页必须把支持信息做清楚，同时保持主操作禁用，避免把本地软件 proof 误解成真实送达、真实手机验收、HIL 或 PR #5 resolution。

本轮用户价值：把最新 `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake` panel 纳入 current-panel fresh-profile browser proof。support reviewer 和普通手机用户应能在本地浏览器门禁里看到同一个 PR #5 thread `PRRT_kwDOSWB9286CJ3tX`、同一个 `hardware_material_pending` 状态、同一个 safe copy 和同一组 false-state flags。

## OKR 映射

| Objective | 本轮关系 | 进度口径 |
| --- | --- | --- |
| Objective 4：手机用户体验与低成本量产边界 | 本轮直接刷新 `mobile/web` current-panel browser proof，覆盖最新 PR #5 reviewer ACK intake panel。 | 保持约 99%，因为这只是 local software proof / browser-gate refresh，不是 true phone/browser proof。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 当前最低约 68%，但本轮不直接推进。 | 保持约 68%，因为仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof、verified terminal result。 |
| Objective 1：硬件协议可信底盘 | PR #5 `hardware_material_pending` thread 是背景证据，但本轮不继续第三轮 material governance rung。 | 保持约 81%，因为 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，且没有真实 LiDAR/ToF、WAVE ROVER/UART 或 HIL。 |

## KR 拆解

| KR | Owner | 需要做什么 | 验收口径 |
| --- | --- | --- | --- |
| KR-A Current-panel browser gate refresh | `full-stack-software-engineer` | 在 `pc-tools/evidence/phone_browser_acceptance_gate.py`、`mobile/test_mobile_web_entrypoint.py`、必要 fixture/docs 中加入 `mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake` capability。 | fresh-profile gate 覆盖 latest panel `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`，显示 `software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate`，console clean，主操作 disabled。 |
| KR-B Robot safe alias consultation | `robot-software-engineer` | 只读确认现有 `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary` 是否足够；必要时只更新接口/产品文档。 | 不新增 raw diagnostic，不新增 robot command side effect，不暴露 `/cmd_vel`、串口、WAVE ROVER/UART、ACK/cursor mutation 或 GitHub mutation。 |
| KR-C Product closeout | `product-okr-owner` | implementation validation 后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。 | 明确 no OKR percentage lift，Objective 5 仍约 68%，并保留 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。 |

## 本轮核心抓手

本轮不是继续推进 PR #5 material governance，而是把已经存在的最新 reviewer ACK intake mobile panel 纳入 current-panel browser proof refresh。核心抓手是 browser gate 对 panel 可见性、boundary 文案、safe copy、fail-closed action state 和 console cleanliness 的覆盖。

## 范围边界

In scope:

- 新增或扩展 browser gate capability：`mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake`。
- 使用 boundary：`software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate`。
- 覆盖 latest panel：`pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`。
- 保留 `PRRT_kwDOSWB9286CJ3tX`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 保持本地 browser-gate / local Chromium-family software proof 口径。

Out of scope:

- 不做第三轮 PR #5 material governance rung。
- 不改硬件配置，不声明真实 WAVE ROVER/UART、LiDAR/ToF、HIL 或实机 powered bench。
- 不声明 true phone/browser proof、真实 iPhone/Android device behavior、production PWA install proof。
- 不声明 O5 external proof、public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、verified terminal result。
- 不声明 route/elevator field pass、Nav2/fixed-route runtime pass 或 delivery success。

## 优先级和验收口径

P0:

- Full-Stack gate 必须能在 fresh-profile browser proof 中覆盖 PR #5 reviewer ACK intake panel。
- 页面和 proof artifact 必须显示 `software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate`。
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 必须保持。

P1:

- Robot consultation 必须确认现有 safe alias 足够，或只补接口/产品文档说明。
- Product closeout 必须在 implementation validation 后同步 sprint final、OKR snapshot 和 okr_progress_log。

P2:

- 如果 fresh-profile gate 已支持 `--capability` / `--evidence-boundary` override，应优先复用，不新增重复 proof script。

## 责任 Engineer

- `full-stack-software-engineer`：主责实现、fixture、focused unit/browser gate 验证。
- `robot-software-engineer`：read-only consultation，确认 Robot safe alias 和接口 side effect 边界。
- `product-okr-owner`：planning docs 和 implementation 后 closeout 文档、OKR/progress log。

## 风险、阻塞和证据链

- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / `hardware_material_pending`；PR #7 open / review threads empty 不能解除该缺口。
- 最近两轮已消费同一 PR #5 hardware-material blocker，本轮必须 pivot，不能第三次继续 material governance wrapper。
- O5 真实进展仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof、verified terminal result；本轮 no OKR percentage lift。
- 本轮证据链只允许写成 local software proof / browser-gate refresh；fresh-profile screenshot/JSON 也不等于真实手机/browser proof。
