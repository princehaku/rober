# Field Evidence Rerun Execution Callback Review Decision PRD

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给低成本 ROS2 小车后，小车能沿固定路线完成送达、电梯 assisted delivery、投放或人工取走，并且每一次结果都有可回放证据。本 sprint 的用户价值不是让机器人真实跑起来，而是把现场 owner 回填的 execution callback intake 结果转成明确的复核决策：哪些材料可继续交接，哪些缺失、被拒或仍 blocked。

## OKR 映射

- Objective 5 仍是数值最低项，约 68%。本 sprint 不直接推进 O5，因为真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和 true phone/browser external proof 不在本机可用。
- Objective 1 仍约 81%。本 sprint 不推进 WAVE ROVER/UART/HIL 或 PR #5 `PRRT_kwDOSWB9286CJ3tX`，因为真实 2D LiDAR / ToF materials、vendor/source/receipt、安装接线、标定和 HIL-entry 材料仍未到位。
- Objective 2/3/4 仍约 99%。本 sprint 只增加 field evidence rerun execution callback review-decision 的软件证明和只读可见性，不写成真实路线、电梯、手机或 delivery success。

## 核心需求

1. PC gate 能消费上一轮 `field_evidence_rerun_execution_callback_intake` artifact/summary 或 Robot safe alias。
2. Gate 输出 `trashbot.field_evidence_rerun_execution_callback_review_decision.v1` artifact 和 `trashbot.field_evidence_rerun_execution_callback_review_decision_summary.v1` summary。
3. Review decision 固定保留 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
4. Robot diagnostics 只暴露 safe alias `robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary`。
5. mobile/web 只读展示 review decision、safe `evidence_ref`、decision reasons、accepted/missing/rejected/blocked material groups、owner handoff、next required evidence 和 evidence boundary。

## 非目标

- 不读取真实材料目录。
- 不访问 ROS graph、Nav2 runtime、电梯、手机/browser、外部云、serial/UART 或 WAVE ROVER。
- 不提交 GitHub review thread 解析、不关闭 PR #5 thread。
- 不启用 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、queue scheduling、execution scheduling、callback submission 或任何机器人控制。

## 验收口径

本 sprint 通过的最低标准是三条链路都能在 Docker/local software proof 范围内 fail closed：

- PC gate 能在 ready/missing/rejected/blocked/unsafe/mismatch/unsupported 输入下生成明确 review decision。
- Robot diagnostics 不泄漏 raw artifact、路径、凭证、ROS topic、serial/UART、WAVE ROVER、checksum、traceback、success/control wording。
- mobile/web 首屏只读 panel 能展示 review decision，但所有主操作仍禁用。
