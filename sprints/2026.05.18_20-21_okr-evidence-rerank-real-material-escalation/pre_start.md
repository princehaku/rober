# Sprint 2026.05.18_20-21 OKR Evidence Rerank Real Material Escalation - Pre Start

## 1. Sprint 声明

- sprint_type: epic
- 启动时间：2026-05-18 20:21 Asia/Shanghai
- 本轮目标：根据近期 PR 和评审重新裁决下一步深入的 OKR，并把无法在 Docker-only 主机继续本地包装的真实材料缺口升级为 owner 可执行清单。
- 证据边界：`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 上轮未完成项

最新 sprint `sprints/2026.05.18_19-20_route-task-acceptance-execution-rerun-result-review-handoff/` 已完成 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`，但 `final.md` 明确剩余真实现场缺口：

- 真实电梯门状态。
- 真实楼层确认。
- 人工协助记录。
- Nav2/fixed-route runtime log。
- 同一 `evidence_ref` 的 task record / completion signal。
- dropoff/cancel completion 或 delivery result。

前一轮 `sprints/2026.05.18_18-19_route-task-acceptance-execution-rerun-result-review-decision/final.md` 已经以同一根因收口：缺真实 route/elevator field materials。按 `AGENTS.md` 同一 Blocker 重复消费红线，第三轮不能继续增加一层本地 route/elevator wrapper。

## 3. PR / Review 证据

- PR #4：`Add elevator-assisted delivery capability to agents, registry and OKR` 已合并，结论是电梯 assisted delivery 进入主链，后续必须补真实 route/elevator 现场材料，而不是只扩展 metadata 层。
- PR #5：`Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 已合并，Codex Review 给出三条具体问题：
  - P1：`docs/product/production_hardware_boundary.md` 的 Default Hardware Set 与 mandatory `monocular + 2D LiDAR + ToF` baseline 矛盾。
  - P2：`OKR.md` 最低 Objective 叙述曾与表格数字不一致，可能误导 sprint routing。
  - P2：新增 2D LiDAR / ToF mandatory sensor 假设缺 `docs/vendor/` 本地来源引用。
- 5/16 硬件系列 sprint 已把 PR #5 问题推进到 baseline review、source alignment、procurement intake/review/execution/receipt、HIL-entry config/readiness/execution pack；没有真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料前，不应继续重复本地硬件 wrapper。

## 4. OKR 排序与切换理由

- 当前 `OKR.md` 4.1 数字最低为 Objective 5，约 68%。本机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；O5 stop rule 继续成立。
- 下一低项 Objective 1 约 81%。本机没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 operator HIL report；PR #5 2D LiDAR / ToF 真实材料也不可用。
- Objective 2 / Objective 3 / Objective 4 已约 99%，但最近两轮都卡在同一 PR #4 真实现场材料缺口。继续堆本地 route/elevator wrapper 会违反同一 Blocker 红线。

本轮因此不做新的本地功能 wrapper，而是启动“真实材料升级/改道决策”sprint：把 O5、O1、PR #4、PR #5 的可恢复条件写成 owner work order；若 CEO 无法提供任何真实材料，则下一轮必须选择不依赖这些材料的新功能切口或明确暂停对应 KR 完成度上调。

## 5. Owner

- Product Manager / OKR Owner：裁决下一轮 OKR 优先级、维护升级说明、定义真实材料验收口径。
- Hardware Infra Engineer：确认 O1 与 PR #5 真实硬件材料清单，不新增未验证硬件事实。
- Autonomy Algorithm Engineer：确认 PR #4 route/elevator 现场材料最小回填包，不新增本地 wrapper。
- User Touchpoint Full-Stack Engineer：确认 O4 真实手机 / PWA / production app 可提交材料清单，不放宽控制按钮。

## 6. 阻塞与边界

- Docker-only：本机没有真实硬件、真实电梯、真实手机、真实公网云材料。
- 本轮不得声称 HIL、真实手机通过、真实 route/elevator field pass、真实投放、delivery success 或 Objective 5 external proof。
- 若后续没有真实材料，本轮收口必须明确 blocked / needs CEO decision，不能把 planning docs 写成 OKR 进度提升。
