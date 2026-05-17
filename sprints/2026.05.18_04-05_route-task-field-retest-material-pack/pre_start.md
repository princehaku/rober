# Sprint 2026.05.18_04-05 Route Task Field Retest Material Pack - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动新 sprint：`2026.05.18_04-05_route-task-field-retest-material-pack`。

目标：在 Docker-only 主机上，承接上一轮 `route_task_field_retest_result_review_handoff`，生成现场 owner 可执行的 `route_task_field_retest_material_pack`。该材料包用于把 PR #4 要求的路线/电梯现场材料采集动作拆成同一 safe `evidence_ref` 下的 checklist、callback skeleton、rerun commands 和 fail-closed 边界，并通过 Robot diagnostics 与 mobile/web 只读展示。

证据边界：`software_proof_docker_route_task_field_retest_material_pack_gate`。本轮不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record/completion signal、真实 dropoff/cancel completion、delivery success、真实手机/browser、HIL 或 Objective 5 external proof。

## 2. 近期 PR / 评审证据

- PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR` 将 elevator assisted delivery 写入主链路和 Phase E，说明 O2/O3 的路线/电梯材料链不是可选增强，而是 MVP 必达能力。
- PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 进一步固化电梯 assisted delivery 和硬件 baseline；Codex Review P1 指出 `docs/product/production_hardware_boundary.md` 默认硬件集与 mandatory `monocular + 2D LiDAR + ToF` baseline 不一致，P2 指出新硬件假设缺 `docs/vendor/` 来源。
- 最新 sprint `2026.05.18_03-04_route-task-result-review-handoff/final.md` 已把 result review decision 推到 owner handoff，但剩余风险仍是缺真实现场 callback 材料、同一 `evidence_ref` 上车复账、真实电梯门状态、真实楼层确认、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。

## 3. OKR 排序与切换理由

当前 `OKR.md` 4.1：

- Objective 5 约 68%，数值最低；但继续推进必须有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 或真实手机/browser external proof。本机只有 Docker，本轮不重复本地 O5 metadata depth。
- Objective 1 约 81%，下一低项；但最近三轮已围绕 WAVE ROVER HIL packet 做 intake / review decision / execution pack，剩余 blocker 是真实 WAVE ROVER、UART、串口日志、topic samples 和 operator HIL report。本轮不第 3 次消费同一真实硬件 blocker。
- Objective 2 / 3 / 4 约 99%，但 PR #4 的真实路线/电梯材料仍未回填。当前最有用的软件推进是把上一轮 handoff 转成现场采集材料包，降低真实回填时的漏项和证据漂移风险。

## 4. Owner 与执行边界

- Task A / Autonomy Algorithm Engineer：新增 PC evidence gate `route_task_field_retest_material_pack`，只消费上一轮 handoff summary/artifact，不读取真实材料目录，不访问 ROS graph、Nav2 runtime、串口、硬件、云或手机。
- Task B / Robot Platform Engineer：在 `operator_gateway_diagnostics.py` 里新增 material pack summary 消费和 fail-closed alias，保持 diagnostics metadata-only。
- Task C / User Touchpoint Full-Stack Engineer：在 `mobile/web` 增加只读“路线/电梯现场材料包”面板和 fixture/test，保持 Start / Confirm / Cancel gating 不变。
- Product / OKR Owner：最终收口 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`，不得把本轮上调成真实 field pass。

## 5. 重复 blocker 检查

最近两轮 `final.md` 均明确 O5 外部证据不可得、O1 真实硬件证据不可得。本轮不继续消费 O5 或 O1 blocker，而是切换到 PR #4 route/elevator field-material 回填准备链。
