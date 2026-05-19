# Sprint 2026.05.19_20-21 Real Material Readiness Board - Pre Start

## 1. sprint_type: epic

本轮是跨 owner 的 Epic Sprint。目标不是继续给某一个已 blocked 的材料链路追加单点 wrapper，而是把 Objective 5 外部材料、Objective 1 / PR #5 硬件材料、PR #4 route/elevator 现场材料、Objective 4 真实手机材料统一成 `real_material_readiness_board`。该 board 必须是只读、fail-closed、可路由的操作员/用户触点，不声明真实 proof，不提高 OKR 百分比。

## 2. 本轮用户价值和产品北极星

北极星：普通手机用户和现场 owner 能一眼看到“下一步缺哪类真实材料、谁负责、什么证据才能推进”，而不是在 O5、O1、PR #4、O4 多条 closeout 文档里来回查找。

用户价值：

- 给现场 owner 一个统一材料看板，减少重复问“到底缺云、硬件、路线、电梯还是手机证据”。
- 给 Robot diagnostics/mobile/web 一个只读路由面，帮助工程团队把下一轮工作指向真实材料，而不是重复本地 software-proof 包装。
- 给 Product closeout 一个明确边界：`software_proof` / `not_proven`，`delivery_success=false`，`primary_actions_enabled=false`，`safe_to_control=false`。

## 3. 已确认证据

- `OKR.md` 4.1：Objective 5 约 68%，是当前最低，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实 external proof。Docker-only 主机无法制造这些材料。
- `OKR.md` 4.1：Objective 1 约 81%，需要真实 WAVE ROVER/UART/HIL，或 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- PR #5 live review thread：`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，原因是 mandatory sensor assumptions lack local vendor/material evidence。
- PR #4 已将 elevator-assisted delivery 合入 mainline；近期 route/elevator sprint 已到 `route_task_field_retest_acceptance_execution_rerun_result_review_handoff` 与 `elevator_field_evidence_trace_material_backfill_review_handoff`，final 均指向真实现场材料，而不是再加本地 wrapper。
- 最新三轮 O4 mobile sprint `17-18 callback intake`、`18-19 callback review decision`、`19-20 callback review handoff` 已连续消费真实手机材料缺口；不应创建第四个单用途 mobile wrapper。

## 4. 上轮未完成项和重复 blocker 核对

上轮 `2026.05.19_19-20_mobile-real-device-acceptance-callback-review-handoff` 已完成只读 handoff，但明确不证明真实手机/browser acceptance、production app、PWA prompt/user choice、O5 external proof、PR #5 硬件材料、WAVE ROVER/UART/HIL、route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success 或 safe-to-control grant。

重复 blocker 结论：

- O5：不能继续本地 cloud metadata depth，除非真实外部材料到位。
- O1 / PR #5：不能关闭 `PRRT_kwDOSWB9286CJ3tX`，除非真实 2D LiDAR / ToF vendor/source/material evidence 到位。
- PR #4 route/elevator：不能再添加单点材料 wrapper，除非有同一 safe `evidence_ref` 的真实现场回填材料。
- O4：不能再添加第四个真实手机单点 wrapper，除非有真实 iPhone/Android 或 production app/browser 材料。

## 5. 本轮核心抓手

创建 `real_material_readiness_board`，把四类材料缺口统一成一个 fail-closed status model：

1. O5 external readiness：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover。
2. O1 / PR #5 hardware readiness：WAVE ROVER/UART/HIL 与 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry。
3. PR #4 route/elevator readiness：真实 task record、route completion signal、Nav2/fixed-route runtime、elevator door/floor/human-assist record、dropoff/cancel completion、delivery result。
4. O4 real phone readiness：真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice、true phone/browser acceptance。

## 6. Owner 和团队分工

- Product Manager / OKR Owner：本轮规划、验收口径、证据边界和 closeout，暂不更新 `OKR.md`，等待工程实现后再收口。
- Robot Platform Engineer：实现 Robot diagnostics 聚合 summary 和接口文档，保证 `primary_actions_enabled=false` 与 `safe_to_control=false` 不被 board 改变。
- User Touchpoint Full-Stack Engineer：实现 mobile/web 只读 board 和 fixture，首屏展示可执行 next_required_evidence，不暴露 raw ROS topic 或 raw JSON。
- Hardware Infra Engineer：实现或补齐 PC-side evidence aggregation 中 PR #5 / O1 硬件材料分类规则，必须引用 `docs/vendor/VENDOR_INDEX.md` 作为硬件事实入口。
- Autonomy Algorithm Engineer：实现或补齐 PR #4 route/elevator / Nav2/fixed-route 材料分类规则，保持 read-only 与 not_proven。

## 7. 验收口径

本轮完成后只允许声明：

- board 能统一展示四类真实材料 readiness 和 next owner。
- Robot diagnostics/mobile/web 能只读消费 board summary。
- 所有 gating flags 仍为 fail-closed：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

本轮不得声明：

- O5 external proof。
- Objective 1 HIL 或 PR #5 hardware material proof。
- PR #4 route/elevator field pass。
- Objective 4 real phone/browser acceptance。
- dropoff/cancel completion、delivery success 或 safe-to-control grant。

## 8. 需要创建或更新的 sprint 文档

本阶段创建：

- `sprints/2026.05.19_20-21_real-material-readiness-board/pre_start.md`
- `sprints/2026.05.19_20-21_real-material-readiness-board/prd.md`
- `sprints/2026.05.19_20-21_real-material-readiness-board/tech-plan.md`

工程完成后再补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
