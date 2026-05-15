# Sprint 2026.05.16_03-04 PC Route Elevator Console Integration - Pre Start

sprint_type: epic

## 1. 启动结论

本轮继续按 live `OKR.md` 4.1 排序。Objective 5 约 66% 是数字最低，但 `OKR.md` 第 6 节和最近两个 final 都明确：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 时，不继续堆本地 O5 metadata。

当前 Docker-only 主机也没有真实 WAVE ROVER/UART/HIL，因此 Objective 1 不能形成 `hil_pass`。最低可行动 Objective 是 Objective 3（约 74%），且最近 `2026.05.16_02-03_elevator-route-evidence-reconciliation/final.md` 的下一步要求把路线进度、task record、completion signal 与电梯复账放到同一 `evidence_ref` 的现场/上车复账链路。

## 2. 本轮目标

交付 `software_proof_docker_pc_route_elevator_console_integration_gate`：

- 让 `pc-tools/route/route_debug_web.py` 可选读取 `elevator_route_evidence_reconciliation` summary/artifact。
- 在 PC route debug HTML/API 中同屏展示 route progress、recent task 和 elevator-route reconciliation 摘要。
- 让 Robot diagnostics 继续 metadata-only 消费 PC console summary，并保留该新增复账字段。
- 让 `mobile/web` 的 PC route debug panel 展示 PC console 已关联的电梯路线复账状态，不改变 Start / Confirm Dropoff / Cancel gating。

## 3. 证据来源

- `OKR.md` 4.1：Objective 5 约 66% 数字最低，但缺真实外部材料；Objective 3 约 74% 是最低 Docker-actionable 功能方向。
- `sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation/final.md`：上一轮新增电梯路线复账，但剩余风险仍是 route/runtime/task record/elevator evidence 需要同屏复核和真实 run 材料。
- `docs/product/mobile_user_flow.md`：已有 PC route debug console panel 与电梯路线复账 panel，但 PC console 自身尚未关联最新复账摘要。
- `pc-tools/route/route_debug_web.py`：当前只读 PC console 只消费 fixed-route status 与 task record，未消费 elevator-route reconciliation。

## 4. Owner 与范围

- Autonomy Algorithm Engineer：PC route debug console 的 route/elevator reconciliation 集成。
- Robot Platform Engineer：diagnostics 对 PC console 新字段的 metadata-only 透传与围栏。
- User Touchpoint Full-Stack Engineer：mobile PC route debug panel 展示新增同屏复账摘要。
- Product Manager / OKR Owner：收口 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint 文档。

## 5. 边界

本轮不访问真实 ROS graph、Nav2 runtime、真实电梯、真实手机、WAVE ROVER、serial/UART、HIL、外部云、OSS/CDN、DB/queue 或 4G。所有输出必须保留 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和 read-only 控制边界。
