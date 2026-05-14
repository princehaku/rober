# Sprint 2026.05.15_02-03 Route Task Field Run Review Console - Pre Start

sprint_type: epic

## 1. 本轮目标

本轮继续从 `OKR.md` 4.1 重新排序。Objective 5 仍是数字最低（约 68%），但当前主机只有 Docker/local 软件环境，缺少能真正推进 O5 的公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 证据。因此本轮不继续叠加 O5 本地 metadata。

本轮切到 Objective 2 / Objective 3 的可执行缺口：上一轮 `software_proof_docker_route_task_field_run_intake_crosscheck_gate` 已经能接收五份现场材料并输出 missing/mismatch/commands_to_rerun，但现场人员仍需要一个可读的复核报告和重跑决策包，把 intake 结果变成“下一次具体补采什么、能不能进入人工复核、为什么不能算 delivery success”的产品化入口。

目标证据边界：`software_proof_docker_route_task_field_run_review_console_gate`。

## 2. 证据来源

- `OKR.md` 4.1：Objective 5 约 68%，但主要缺口是外部真实材料；Objective 2 / Objective 3 约 84%，主要缺口是真实 Nav2/fixed-route、真实路线采集、同一 `evidence_ref` 上车复账和 delivery success。
- `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/final.md`：上一轮完成 intake/crosscheck，但明确剩余风险是仍需真实 route status、task record、runtime log、robot-side task evidence 和 mobile summary 才能进入真实 field run 复账。
- `pc-tools/README.md`：field-run readiness 和 intake 已有 CLI 契约，但当前缺少面向 operator/support 的“复核报告/重跑决策”层。
- 近期反复问题：O5 外部证明不可用、O1/HIL 无真实硬件、O2/O3 软件链路持续缺同一 `evidence_ref` 的真实运行材料；所有新材料必须保持 `not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

## 3. 本轮 Owner

- `autonomy-engineer`：新增 field-run review console/report CLI，负责 PC/evidence 侧 schema、report、tests 和 navigation/PC 文档。
- `robot-software-engineer`：把 review report 作为 diagnostics metadata-only summary 消费，证明不触发动作、ACK、cursor、HIL 或 delivery success。
- `full-stack-software-engineer`：在 `mobile/web` 首屏增加只读 field-run review panel，展示重跑决策和 safe copy，不改变 Start/Confirm/Cancel gating。
- `product-okr-owner`：工程完成后更新 closeout、OKR 和 progress log。

## 4. 风险边界

- 本轮不访问硬件、串口、ROS graph、Nav2 runtime、外部云、OSS/CDN、DB/queue 或 4G。
- 本轮不证明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、HIL、dropoff/cancel completion、delivery success 或 O5 external proof。
- 如实现中发现只能重复上一轮 intake 字段而没有新增 operator decision/user value，应停止扩展并收口为 blocked，而不是为了更新 OKR 继续叠 wrapper。
