# Sprint 2026.05.20_15-16 Field Evidence Rerun Callback Review Handoff - Pre Start

## 1. Sprint 声明

- sprint_type: epic
- 主题：`field_evidence_rerun_callback_review_handoff`
- 启动时间：2026-05-20 15:03 Asia/Shanghai
- owner：Autonomy Algorithm Engineer、Robot Platform Engineer、User Touchpoint Full-Stack Engineer、Product Manager / OKR Owner

## 2. 上轮状态

- 最新 sprint `2026.05.20_14-15_field-evidence-rerun-callback-review-decision` 已完成 `field_evidence_rerun_callback_review_decision`。
- 已有边界：`software_proof_docker_field_evidence_rerun_callback_review_decision_gate`、`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 上轮输出包含 review decision、owner handoff、next required evidence、rerun guidance 和 blocker summary，但还没有把这些结论打包成可交接给现场 owner 的 handoff artifact / summary。

## 3. 近期 PR / 评审证据

- `OKR.md` 4.1 当前显示 Objective 5 约 68%，仍是最低项；但下一步 completion 依赖真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof，本机 Docker-only 无法提供。
- PR #5 review thread live 状态：`PRRT_kwDOSWB9286CJ3tQ` 和 `PRRT_kwDOSWB9286CJ3tU` 已 resolved；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false`，要求 vendor/source 和真实 2D LiDAR / ToF material。已发布 manual reply `3269642220`，但这不是硬件 proof。
- 最近 `12-13`、`13-14`、`14-15` 三轮已经从 field evidence material dispatch 推进到 callback intake、callback review decision；下一步可执行功能不是重复 blocker，而是把 review decision 转成 handoff 包，明确谁补什么材料、如何 rerun、何时回填。

## 4. 本轮目标

建立 `software_proof_docker_field_evidence_rerun_callback_review_handoff_gate`：

- Autonomy 提供 PC handoff gate，读取 `field_evidence_rerun_callback_review_decision` artifact / summary，输出 handoff artifact / summary。
- Robot diagnostics 提供 safe alias `robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary`，只读暴露 handoff summary。
- mobile/web 提供只读“现场证据复跑复核交接”panel，展示 handoff owner、handoff reason、next required evidence、rerun commands 和 blocker summary，不启用任何主操作。
- Product closeout 保持 OKR 边界：不提高 O5 / O1，不把本轮写成真实 route/elevator field pass、真实手机/browser、HIL、delivery success 或 PR #5 resolved。

## 5. 风险边界

- 本机没有真实硬件，只有 Docker；本轮只能形成 software proof。
- 不触发 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
- 不新增真实控制能力，不改变 Start Delivery / Confirm Dropoff / Cancel gating。
