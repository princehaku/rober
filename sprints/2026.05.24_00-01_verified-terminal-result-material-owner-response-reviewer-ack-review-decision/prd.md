# Verified Terminal Result Material Owner Response Reviewer ACK Review Decision PRD

Run time: 2026-05-24 00:01 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 1. 用户价值和产品北极星

北极星：让普通手机用户和支持团队看到安全、清晰、可复盘的远程控制与终态材料链路；任何材料复核状态都不能越权变成真实送达、真实云、真实手机、HIL 或控制授权。

本轮用户价值：

- 支持同学能看到 reviewer ACK intake 之后的明确 review decision，而不是只知道“有人 ACK 了”。
- field owner 能知道下一步是补材料、重分配、进入 review handoff，还是因为 unsafe / evidence-ref mismatch 被阻断。
- 手机用户不会被 software_proof 状态误导；Start Delivery、Confirm Dropoff、Cancel 继续保持 disabled。
- Product closeout 能继续说明 Objective 5 为什么仍约 68%，以及为什么这轮不应提升 OKR 百分比。

## 2. OKR 映射

- Objective 5：主目标。该 sprint 继续 verified terminal-result material evidence workflow，把 reviewer ACK intake 推进到 reviewer ACK review decision。当前进度约 68%，仍是最低 Objective。
- Objective 1：只保留硬件材料边界。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，仍缺真实 2D LiDAR / ToF SKU/source/receipt、安装、接线、电源、标定、HIL-entry、WAVE ROVER/UART/HIL、operator report 和 reviewer resolution。
- Objective 4：只涉及手机 read-only 展示与 fail-closed 体验。它不是真实 iPhone/Android device behavior，不是真实 PWA prompt/userChoice，也不是真实手机/browser proof。
- Objective 2/3：不改变 route/elevator、Nav2、fixed-route、dropoff/cancel、task record 或 delivery result。

## 3. KR 拆解或更新

本轮不更新 `OKR.md`，只规划后续实现与 closeout 的 KR 证据口径。

- KR-O5-A：PC gate 能从 `verified_terminal_result_material_owner_response_reviewer_ack_intake` 安全生成 reviewer ACK review-decision artifact 和 summary。
- KR-O5-B：Robot diagnostics 暴露 `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary` safe alias，不泄露 raw materials、凭证、ROS/control、串口、WAVE ROVER 或本地路径。
- KR-O5-C：`mobile/web` 增加 read-only panel，只显示 safe decision、safe IDs、next required evidence、PR #5 unresolved status 和 false-state flags。
- KR-O5-D：Product closeout 同步 sprint 留档、`OKR.md` 与 `docs/process/okr_progress_log.md`，并明确 no OKR percentage lift，除非实现阶段额外拿到真实外部/硬件/手机/field/HIL 证据。

## 4. 本轮核心抓手

核心抓手是 `verified_terminal_result_material_owner_response_reviewer_ack_review_decision`，它把上一轮 reviewer ACK intake 的安全元数据转成明确的 review decision。

允许 decision 示例：

- `accepted_for_reviewer_ack_review_not_proven`
- `missing_material_for_reviewer_ack_review_not_proven`
- `needs_reassignment_for_reviewer_ack_review_not_proven`
- `blocked_missing_reviewer_ack_intake`
- `reviewer_ack_review_evidence_ref_mismatch`
- `reviewer_ack_review_rejected_unsafe`

所有 decision 都必须保留：

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## 5. 需要做什么

实现阶段需要做：

- 新增 PC gate：读取安全 reviewer ACK intake metadata，输出 review-decision artifact / summary，并对 unsafe raw fields、success claims、control claims、PR #5 resolved claims fail closed。
- 新增 Robot safe alias：把 PC summary 转成 diagnostics/status 可消费的 safe summary。
- 新增 mobile read-only panel：展示 review decision、safe `evidence_ref`、safe `command_id`、owner/support/reviewer route、missing/rejected classifications、next required evidence、PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / hardware_material_pending，保持主操作 disabled。
- 同步相关 docs：接口文档、operator diagnostics 文档、mobile user flow、remote 4G MVP / cloud boundary 相关段落。
- closeout 阶段由 Product 更新 sprint `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 6. 优先级和验收口径

Priority P0:

- PC gate 和 Robot/mobile summary 必须在同一 safe `evidence_ref` 下表达 reviewer ACK review decision。
- 必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 必须明确 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`。
- 必须 fail closed：raw artifact、credentials、Authorization、signed URL、local path、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER details、traceback、checksum、complete artifact、success/control wording、PR resolved wording 均不得出现在 safe output。

Priority P1:

- Mobile panel 文案中文优先，read-only，不能新增 fetch raw diagnostics/material/review/handoff/owner-response/reviewer-ACK routes，也不能新增控制路径。
- Robot alias 应保持现有 diagnostics/status pattern，不引入 ACK/cursor mutation 或 command replay。

Planning acceptance for this Product run:

- 三份 planning 文件存在。
- planning docs 包含 Objective 5、OKR 最低优先级核对、PR #5 thread evidence、software proof boundary、false-state flags 和 no-real-proof 边界。
- scoped `git diff --check` 通过。

Implementation acceptance for later workers:

- Targeted PC/Robot/mobile unit tests pass.
- `py_compile` / `node --check` / fixture `json.tool` pass for touched files.
- Required `rg` proves capability name, evidence boundary, false-state flags, PR #5 unresolved status, and forbidden-success wording boundary exist in touched surfaces.
- Scoped `git diff --check` passes for touched files.

## 7. 对应责任 Engineer

- `full-stack-software-engineer`: PC gate and mobile read-only panel.
- `robot-software-engineer`: Robot diagnostics safe alias and status/diagnostics integration.
- `product-okr-owner`: sprint record, Product acceptance, OKR/progress-log closeout.
- `robot-hardware-engineer`: no implementation owner in this sprint unless real PR #5 hardware materials appear; if materials appear, Hardware must verify them against `docs/vendor/VENDOR_INDEX.md` and referenced local vendor files before any hardware claim.
- `autonomy-engineer`: no implementation owner in this sprint unless route/elevator/Nav2/fixed-route evidence appears; if it appears, Autonomy must keep field evidence separate from software proof.

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

- `sprints/2026.05.24_00-01_verified-terminal-result-material-owner-response-reviewer-ack-review-decision/pre_start.md`
- `sprints/2026.05.24_00-01_verified-terminal-result-material-owner-response-reviewer-ack-review-decision/prd.md`
- `sprints/2026.05.24_00-01_verified-terminal-result-material-owner-response-reviewer-ack-review-decision/tech-plan.md`

Implementation closeout must later create or update:

- `sprints/2026.05.24_00-01_verified-terminal-result-material-owner-response-reviewer-ack-review-decision/tech-done.md`
- `sprints/2026.05.24_00-01_verified-terminal-result-material-owner-response-reviewer-ack-review-decision/side2side_check.md`
- `sprints/2026.05.24_00-01_verified-terminal-result-material-owner-response-reviewer-ack-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
