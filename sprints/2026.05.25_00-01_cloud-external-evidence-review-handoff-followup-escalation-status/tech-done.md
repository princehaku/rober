# Tech Done

- sprint_type: epic
- sprint: `2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status`
- target capability: `cloud_external_evidence_review_handoff_followup_escalation_status`
- upstream capability: `cloud_external_evidence_review_handoff`
- upstream review decision: `cloud_external_evidence_review_decision`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate`
- closeout time: 2026-05-25 00:25 Asia/Shanghai

## 用户价值和产品北极星

本轮把 O5 external evidence review handoff 之后的跟进状态做成可见、可复核、可升级的只读 accountability rung。用户价值不是让机器人开始执行，而是让 owner、support、reviewer 和 CEO 能看到 handoff 是否 pending / due / overdue / escalated / blocked，知道下一步需要补哪类真实外部证据，并避免把 PR #5 `PRRT_kwDOSWB9286CJ3tX` 的 `hardware_material_pending` 误读成已解决。

产品北极星仍是普通手机用户可理解、可诊断、可恢复的垃圾投递闭环。本轮只改善云外部证据责任链的可解释性，不改变真实送达、真实手机、真实云或硬件验收状态。

## OKR 映射与 KR 拆解

- Objective 5 仍是最低完成度方向，保持约 68%。
- KR1：保持不暴露 `/cmd_vel`，不新增 inbound robot control。
- KR2：继续只记录缺失云基础设施证据，不声明 4C 8G production baseline live。
- KR3/KR4：OSS/CDN 只作为下一步 required evidence；本轮无 OSS/CDN live traffic。
- KR5：不接收凭证、signed URL、raw artifact 或 GitHub mutation。
- KR6：把缺失外部证据转成 owner/support/reviewer action 和 CEO escalation recommendation，同时保持 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

本轮 `no OKR percentage lift`。Objective 1 保持约 81%，Objective 2/3/4 保持约 99%，Objective 5 保持约 68%。

## 实际改动

Task A Full-Stack Engineer 已完成：

- `pc-tools/evidence/cloud_external_evidence_review_handoff_followup_escalation_status.py`
- `pc-tools/evidence/test_cloud_external_evidence_review_handoff_followup_escalation_status.py`
- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status.json`
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`

Task A 产物新增 PC evidence gate，输出 `cloud_external_evidence_review_handoff_followup_escalation_status` 和 `robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary`；`mobile/web` 只读 panel 展示 source handoff status、due/overdue/escalated、blocked reason、owner/support/reviewer action、CEO escalation recommendation、next required evidence、`PRRT_kwDOSWB9286CJ3tX`、`hardware_material_pending` 和 false-state flags。未新增 upload、review mutation、GitHub mutation、diagnostics fetch 或 robot control path。

Task B Robot Platform Engineer 已完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

Task B 新增 `robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary` safe alias，只接受 sanitized capability / summary / robot alias payload，保留 source capability `cloud_external_evidence_review_handoff` 和 upstream `cloud_external_evidence_review_decision`，并拒绝或忽略 raw command/control、ACK/cursor mutation、production endpoint、signed URL、`/cmd_vel`、serial/UART/WAVE ROVER 和 success/completion claims。

Task C Product closeout 本轮只更新：

- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/tech-done.md`
- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Task A reported validation:

- `python3 -m py_compile pc-tools/evidence/cloud_external_evidence_review_handoff_followup_escalation_status.py` passed.
- `python3 -m unittest pc-tools/evidence/test_cloud_external_evidence_review_handoff_followup_escalation_status.py` output `Ran 5 tests ... OK`.
- `python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status.json` passed.
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_external_evidence_review_handoff_followup_escalation_status` output `Ran 2 tests ... OK`.
- Required `rg` passed.
- Scoped `git diff --check` passed.
- Extra `node --check mobile/web/app.js` passed.

Task B reported validation:

- `py_compile` exit 0.
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py -k cloud_external_evidence_review_handoff_followup_escalation_status` output `Ran 1 test in 0.020s OK`.
- Required `rg` passed.
- Scoped `git diff --check` passed.

Task C closeout validation:

- Required closeout `rg` passed.
- Scoped `git diff --check -- sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status OKR.md docs/process/okr_progress_log.md` passed.

## Docs 同步核对

Task A/B 已同步 docs：

- `docs/product/mobile_user_flow.md` 已记录 `cloud_external_evidence_review_handoff_followup_escalation_status` 手机只读 panel、fallback summary、禁用 Start Delivery / Confirm Dropoff / Cancel、`not true phone/browser proof` 和 `no OKR percentage lift`。
- `docs/product/remote_4g_mvp.md` 已记录 O5 external evidence follow-up escalation status 的 remote/phone-safe 产品边界。
- `docs/interfaces/ros_runtime_contracts.md` 已记录 `robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary` safe alias、允许字段和拒绝边界。

Product closeout 接受 docs 同步状态，不改产品代码、不改测试代码、不改硬件配置。

## 未完成事项与风险

- 本轮是 Docker/local `software_proof` only，`not_proven`。
- Not true phone/browser proof；未跑真实 iPhone/Android、真实 PWA prompt/userChoice 或 production app。
- Not external proof；未证明 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或多实例一致性。
- Not HIL、not WAVE ROVER/UART proof、not route/elevator field pass、not verified terminal result、not delivery success。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`，本轮不作为 PR #5 resolution。
- No product action enables Start Delivery、Confirm Dropoff、Cancel、ACK/cursor mutation、material upload、GitHub mutation、diagnostics fetch 或 robot control。
