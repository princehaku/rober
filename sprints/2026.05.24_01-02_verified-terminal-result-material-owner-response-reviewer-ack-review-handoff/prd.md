# Verified Terminal Result Material Owner Response Reviewer ACK Review Handoff PRD

Run time: 2026-05-24 01:02 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 1. 用户价值和产品北极星

北极星：让普通手机用户和支持团队看到安全、清晰、可复盘的远程控制与终态材料链路；任何 reviewer ACK handoff 状态都不能越权变成真实送达、真实云、真实手机、HIL、PR #5 resolved 或控制授权。

本轮用户价值：

- field owner、support owner 和 reviewer 能拿到一份从 `verified_terminal_result_material_owner_response_reviewer_ack_review_decision` 派生的安全交接包，明确谁跟进、缺什么、下一步回填什么。
- Product 可以把 Objective 5 的下一步写清楚：这是为真实外部材料 follow-up 做交接准备，不是 real terminal result 或 O5 external proof。
- 手机用户不会被 handoff metadata 误导；Start Delivery、Confirm Dropoff、Cancel 继续 disabled，页面只读展示 `not_proven`。
- Reviewer 能看到 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 is_resolved=false / `hardware_material_pending`，不会把 Q/U resolved 误读成全部 review threads closed。

## 2. OKR 映射

- Objective 5：主目标。当前约 68%，仍是 `OKR.md` 4.1 中最低 Objective。本轮只规划 `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`，用于把 reviewer ACK review-decision safe metadata 转成 owner/support/reviewer handoff safe artifact；no OKR percentage lift。
- Objective 1：只保留硬件材料边界。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，仍缺真实 2D LiDAR / ToF SKU/source/receipt、采购、安装、接线、电源、标定、HIL-entry、WAVE ROVER/UART/HIL、operator report 和 reviewer resolution。
- Objective 4：只涉及手机 read-only 展示与 fail-closed 体验。它不是真实 iPhone/Android device behavior，不是真实 PWA prompt/userChoice，也不是真实手机/browser proof。
- Objective 2/3：不改变 route/elevator、Nav2、fixed-route、task record、terminal result、dropoff/cancel、delivery result 或 real field execution。

## 3. KR 拆解或更新

本轮 Product planning 不更新 `OKR.md`，只定义后续实现与 closeout 的 KR 证据口径。

- KR-O5-A：Autonomy/PC evidence gate 能从 reviewer ACK review-decision safe metadata 生成 `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff` artifact / summary。
- KR-O5-B：Robot diagnostics 暴露 `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary` safe alias，不泄露 raw materials、凭证、ROS/control、串口、WAVE ROVER、ACK/cursor 或本地路径。
- KR-O5-C：`mobile/web` 增加 read-only panel，只显示 handoff status、safe IDs、owner/support/reviewer route、next required evidence、PR #5 unresolved status 和 false-state flags。
- KR-O5-D：Product closeout 在实现证据回来后同步 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`，并明确 no OKR percentage lift，除非真实外部/硬件/手机/field/HIL 证据实际到位。

## 4. 本轮核心抓手

核心抓手是 `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`，它把上一轮 reviewer ACK review decision 的安全元数据转成 owner/support/reviewer handoff safe artifact。

允许 handoff 状态示例：

- `ready_for_real_material_reviewer_handoff_not_proven`
- `handoff_missing_material_not_proven`
- `handoff_needs_reassignment_not_proven`
- `blocked_missing_reviewer_ack_review_decision_not_proven`
- `reviewer_ack_handoff_evidence_ref_mismatch_not_proven`
- `reviewer_ack_handoff_rejected_unsafe`

所有状态都必须保留：

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## 5. 需要做什么

实现阶段需要做：

- 新增 PC gate：读取安全 reviewer ACK review-decision metadata，输出 handoff artifact / summary，并对 unsafe raw fields、success claims、control claims、PR #5 resolved claims fail closed。
- 新增 Robot safe alias：把 PC summary 转成 diagnostics/status 可消费的 safe summary。
- 新增 mobile read-only panel：展示 handoff status、safe `evidence_ref`、safe `command_id`、owner/support/reviewer route、missing/rejected classifications、next required evidence、PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`，保持主操作 disabled。
- 同步相关 docs：接口文档、operator diagnostics 文档、mobile user flow、remote 4G MVP / cloud boundary 相关段落。
- closeout 阶段由 Product 更新 sprint `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 6. 优先级和验收口径

Priority P0:

- PC gate、Robot summary、mobile panel 必须在同一 safe `evidence_ref` 下表达 reviewer ACK review handoff。
- 必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 必须明确 `PRRT_kwDOSWB9286CJ3tX` 仍 is_resolved=false / `hardware_material_pending`。
- 必须 fail closed：raw artifact、credentials、Authorization、signed URL、local path、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER details、traceback、checksum、complete artifact、success/control wording、PR resolved wording 均不得出现在 safe output。

Priority P1:

- Mobile panel 文案中文优先，read-only，不能新增 fetch raw diagnostics/material/review/handoff/owner-response/reviewer-ACK routes，也不能新增控制路径。
- Robot alias 应保持现有 diagnostics/status pattern，不引入 ACK/cursor mutation、GitHub mutation、material upload 或 command replay。
- Product closeout 必须把该 sprint 写成 external-material follow-up handoff readiness，而不是业务闭环。

Planning acceptance for this Product run:

- 三份 planning 文件存在。
- planning docs 包含 Objective 5、OKR 最低优先级核对、PR #5 thread evidence、software proof boundary、false-state flags、handoff capability name 和 no-real-proof 边界。
- scoped `git diff --check` 通过。

Implementation acceptance for later workers:

- Targeted PC/Robot/mobile unit tests pass.
- `py_compile` / `node --check` / fixture `json.tool` pass for touched files.
- Required `rg` proves capability name, evidence boundary, false-state flags, PR #5 unresolved status, and forbidden-success wording boundary exist in touched surfaces.
- Scoped `git diff --check` passes for touched files.

## 7. 对应责任 Engineer

- `autonomy-engineer`: Task A Autonomy/PC evidence gate, focused tests, PC README, and interface docs.
- `robot-software-engineer`: Task B Robot diagnostics safe alias and status/diagnostics integration.
- `full-stack-software-engineer`: Task C mobile/web read-only panel, fixture, tests, and mobile flow docs.
- `product-okr-owner`: Task D closeout after implementation evidence: sprint records, Product acceptance, `OKR.md`, and progress-log.
- `robot-hardware-engineer`: no implementation owner in this sprint unless real PR #5 hardware materials appear; if materials appear, Hardware must verify them against `docs/vendor/VENDOR_INDEX.md` and referenced local vendor files before any hardware claim.

## 8. 风险、阻塞和需要补齐的证据链

Known blockers:

- No real hardware on this host; only Docker/local execution is available.
- No real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or external cloud proof.
- No true phone/browser proof, real iPhone/Android device behavior, production app, or PWA prompt/userChoice proof.
- No real 2D LiDAR / ToF SKU/source/receipt, procurement, installation, wiring, power, calibration, HIL-entry, WAVE ROVER powered bench, UART/HIL logs, operator HIL report, or reviewer resolution.
- No real route/elevator field pass, Nav2/fixed-route runtime pass, verified terminal delivery/dropoff/cancel result, dropoff completion, cancel completion, delivery result, or delivery success.

Evidence that must be collected before OKR lift:

- For Objective 5: real public ingress/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, or verified terminal delivery/dropoff/cancel result.
- For Objective 1: PR #5 `PRRT_kwDOSWB9286CJ3tX` real 2D LiDAR / ToF and WAVE ROVER/UART/HIL evidence plus reviewer resolution.
- For Objective 2/3/4: real task record, route completion signal, Nav2/fixed-route runtime log, elevator door/floor evidence, dropoff/cancel completion, delivery result, and true mobile-device evidence.

## 9. 需要创建或更新的 sprint 文档

Created in this planning run:

- `sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/pre_start.md`
- `sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/prd.md`
- `sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/tech-plan.md`

Implementation closeout must later create or update:

- `sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/tech-done.md`
- `sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/side2side_check.md`
- `sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
