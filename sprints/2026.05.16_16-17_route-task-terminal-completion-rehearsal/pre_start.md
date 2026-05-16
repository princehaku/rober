# Sprint 2026.05.16_16-17 Route Task Terminal Completion Rehearsal - Pre Start

sprint_type: epic

## 1. 启动背景

本轮按 CEO 要求“开始下一轮迭代，根据近期 PR 和评审，建议下一步应深入的 OKR；用 team 继续完成 OKR；重新在功能往前走；优先推进 OKR 完成度低的部分；本机没有真实硬件，只有 Docker”启动。

当前 `OKR.md` 4.1 显示 Objective 5 约 66% 为最低，但下一步能真正提升 O5 的证据仍是公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。本机只有 Docker，继续新增 O5 local metadata 不能构成外部 proof。

Objective 1 约 73%，但真实 WAVE ROVER、UART、Orange Pi 串口、`T=1001` feedback 和 HIL 仍不可用。本轮不消费“缺真实硬件”这个 blocker。

## 2. 近期 PR / 评审证据

- PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 把电梯 assisted delivery 写入主 OKR 与 agent 职责，说明 O2/O3 的 route/elevator 主链必须继续进入可执行工程链路。
- PR #5 review P1 指出 `docs/product/production_hardware_boundary.md` 默认硬件集与 mandatory `monocular + 2D LiDAR + ToF` baseline 曾矛盾，会误导 BOM、采购和 bringup。
- PR #5 review P2 指出 OKR lowest narrative 曾与表格数值不一致，会误导 sprint routing；本轮必须显式写清 O5 最低但外部阻塞。
- PR #5 review P2 指出 mandatory sensor assumptions 必须引用 `docs/vendor/` 来源；最近硬件链已连续处理到 receipt intake，但真实材料仍未到位。

## 3. 最近 sprint 证据

- `sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake/final.md`：硬件材料链已到 receipt intake，但仍缺真实 SKU/source/receipt、采购、安装、接线、电源、标定和 HIL-entry。
- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/final.md`：O2/O3 下一步应补同一 `evidence_ref` 的 Nav2/fixed-route runtime log、task record、route completion signal、门状态、楼层确认、人工协助记录、dropoff/cancel completion 和 delivery result。
- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/final.md`：现场材料链已形成 retest request，但真实 route/elevator field pass、真实 dropoff/cancel completion 和 delivery success 仍缺。

## 4. 本轮目标

本轮选择 Objective 2 / Objective 3 的可行动作：`route_task_terminal_completion_rehearsal`。

目标是在 Docker-only 环境中，把 `task_orchestrator` 的 dry-run / manual-confirm / cancel 终态、`task_record`、既有 `route_task_completion_signal`、Robot diagnostics 和 mobile/web 只读摘要串成同一 `evidence_ref` 的 software proof，形成“任务终态复账”能力。

本轮证据边界固定为：

- `software_proof_docker_route_task_terminal_completion_rehearsal_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 5. Owner

- Robot Platform Engineer：task record / diagnostics 终态复账字段。
- Autonomy Algorithm Engineer：PC evidence gate 和 route/task completion signal 复账。
- User Touchpoint Full-Stack Engineer：mobile/web 只读任务终态复账 panel。
- Product Manager / OKR Owner：closeout、OKR 和进度日志。

## 6. 风险边界

本轮不证明真实 Nav2/fixed-route、真实电梯、真实路线采集、真实 dropoff completion、真实 cancel completion、delivery success、真实手机/browser、production app、WAVE ROVER/UART/HIL 或 Objective 5 external proof。

如果 worker 只能产生 local artifact 或 phone-safe summary，正确收口是 software proof / not_proven，而不是提升真实 completion 或 HIL。
