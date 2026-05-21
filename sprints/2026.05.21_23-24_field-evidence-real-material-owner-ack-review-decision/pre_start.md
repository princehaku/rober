# Field Evidence Real Material Owner Ack Review Decision Pre-Start

## Sprint Type

- sprint_type: epic
- sprint_path: `sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/`
- capability: `field_evidence_real_material_owner_ack_review_decision`
- evidence_boundary: `software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate`
- fixed_status: `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`
- run_context: macOS host with Docker/local proof only; no real hardware, no true phone/browser proof, no public cloud proof, no route/elevator field pass, and no HIL.

## 背景证据

- `OKR.md` 4.1 current lowest Objective is Objective 5 at about 68%.
- Latest sprint `2026.05.21_22-23_cloud-ack-lookup-pending-status-guard` closed `software_proof_docker_cloud_ack_lookup_pending_status_guard`; it explicitly did not provide real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, or delivery success.
- Previous field-material sprint `2026.05.21_21-22_field-evidence-real-material-owner-ack-intake` closed `software_proof_docker_field_evidence_real_material_owner_ack_intake_gate`; it converted material followup escalation into structured owner acknowledgement intake.
- PR #5 live review boundary remains unchanged: `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved, while `PRRT_kwDOSWB9286CJ3tX` is still `is_resolved=false`; real 2D LiDAR / ToF vendor, source, receipt, procurement, installation, wiring, power, calibration, and HIL-entry evidence remains missing.
- Hardware facts must continue to cite `docs/vendor/VENDOR_INDEX.md` as the local entry point. This sprint may consult vendor boundaries, but it must not invent pin, voltage, UART, speed, feedback, or mechanical claims.

## 用户价值和产品北极星

用户价值：现场 owner 已经 acknowledgement 之后，支持人员需要一个结构化复核决策，把 ack 明确转成 `accepted`、`needs_more_evidence` 或 `rejected`，并给出下一步材料要求，而不是让手机、Robot diagnostics 或 PC 工具把 ack 误读成真实现场通过。

产品北极星：普通手机用户和现场支持人员只看到可执行、可追溯、fail-closed 的材料复核状态；任何 owner ack review decision 都不能替代真实 route/elevator field pass、真实手机、真实 HIL、O5 external proof 或 delivery success。

## OKR 映射

- Objective 5：不推进 completion。O5 仍约 68%，但继续提高必须依赖真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser 外部材料；本轮不再堆同类本地 metadata wrapper。
- Objective 2：为真实送达 / 电梯 assisted delivery 的材料链增加 owner ack 复核决策入口，但不证明真实送达、dropoff/cancel completion、route/elevator field pass 或 delivery success。
- Objective 3：为 Nav2 / fixed-route runtime log、route completion signal、task record 等现场材料提供复核决策承接，但不证明真实路线实跑。
- Objective 4：手机端只读显示 owner ack review decision，保持 Start Delivery / Confirm Dropoff / Cancel fail-closed，不证明真实手机/browser 或 production app。
- Objective 1：不提高。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；本轮不提供真实 2D LiDAR / ToF、WAVE ROVER、UART、HIL-entry 或 reviewer resolution。

## KR 拆解或更新

- KR-A：PC evidence gate 将上一轮 `field_evidence_real_material_owner_ack_intake` 的 owner ack 转为 review decision，输出 `accepted` / `needs_more_evidence` / `rejected`，并保留 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- KR-B：Robot diagnostics 增加 safe alias / summary，只暴露 decision、safe `evidence_ref`、missing material groups、next evidence、owner handoff 和 proof boundary，不暴露 raw artifacts、ROS topics、serial/UART、WAVE ROVER details、credentials 或 success wording。
- KR-C：mobile/web 增加只读 panel / fixture / tests，展示 owner ack review decision，并保持主操作按钮不可用。
- KR-D：Hardware 完成只读 vendor / PR #5 boundary consultation，确认本轮不改变硬件配置、不声称 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved、不声称 HIL-entry。

## 本轮核心抓手

核心抓手是 `field_evidence_real_material_owner_ack_review_decision`：把 owner acknowledgement intake 升级成结构化复核决策，帮助现场材料链进入下一步 backfill / rerun / escalation，而不是停在“有人确认收到”的元数据状态。

## 需要做什么

- 创建 PC gate `pc-tools/evidence/field_evidence_real_material_owner_ack_review_decision.py`，解析 owner ack intake artifact 或 fixture，校验 schema、safe evidence ref、source boundary 和 required material groups。
- 增加 Autonomy tests / docs，覆盖 accepted、needs_more_evidence、rejected、bad schema、unsafe copy、missing evidence、success-claim rejection。
- 在 Robot behavior diagnostics 中增加 `robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary` safe alias / summary 和 tests / docs。
- 在 mobile/web 增加只读 panel、fixture、测试和 `docs/product/mobile_user_flow.md` 更新；panel 不触发 ACK、cursor、diagnostics fetch 或任何 robot command。
- Hardware 只读核对 `docs/vendor/VENDOR_INDEX.md`、PR #5 thread boundary 和 production hardware boundary；除非发现计划必须修正的硬件资料引用缺口，否则不做实现改动。

## 优先级和验收口径

- P0：四个 owner 并行启动，文件范围互不重叠；任何 implementation 必须由对应 Engineer 子 agent 完成。
- P0：输出必须固定 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- P0：`accepted` 仅表示 owner ack materials structurally accepted for next review/backfill step，不得写成 field pass、delivery result、HIL 或 PR #5 resolution。
- P0：`needs_more_evidence` 必须列出缺失材料并保持 fail-closed。
- P0：`rejected` 必须给出拒绝原因和下一步 owner action。
- P1：mobile/web 和 Robot diagnostics copy 使用中文优先，且过滤 raw JSON、ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER details、credentials、local paths、complete artifacts、checksums、HIL/pass wording、delivery success claims。

## 对应责任 Engineer

- Autonomy Algorithm Engineer：PC evidence gate、evidence tests、PC evidence docs。
- Robot Platform Engineer：onboard behavior diagnostics safe alias / summary、diagnostics tests、interface docs。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、tests、product-flow docs。
- Hardware Infra Engineer：read-only vendor / PR #5 boundary consultation；默认 no implementation changes。
- Product Manager / OKR Owner：sprint chain、OKR boundary、final closeout、progress-log decision。

## 风险、阻塞和需要补齐的证据链

- Objective 5 blocker: still no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, or delivery success.
- Objective 1 blocker: PR #5 `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false`; missing true 2D LiDAR / ToF source, receipt, procurement, installation, wiring, power, calibration, HIL-entry, WAVE ROVER/UART logs, and reviewer resolution.
- O2/O3/O4 blocker: still no true task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor evidence, human-assistance note, dropoff/cancel completion, delivery result, true phone/browser evidence, or route/elevator field pass under the same safe `evidence_ref`.
- This sprint can only produce Docker/local software proof and structured decision readiness. It cannot prove real hardware, real field execution, real mobile device behavior, or production cloud readiness.

## 需要创建或更新的 sprint 文档

- Current planning phase creates:
  - `pre_start.md`
  - `prd.md`
  - `tech-plan.md`
- Implementation phase must later create:
  - `tech-done.md`
  - `side2side_check.md`
  - `final.md`
