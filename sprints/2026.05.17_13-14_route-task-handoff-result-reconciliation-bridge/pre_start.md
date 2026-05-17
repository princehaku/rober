# Sprint 2026.05.17_13-14 Route Task Handoff Result Reconciliation Bridge - Pre Start

sprint_type: epic

## 1. 启动背景

本轮按 `OKR.md` 4.1 重新排序。当前 Objective 5 仍是数值最低（约 68%），但 `OKR.md` 第 6 节要求只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser 材料时才继续推进 O5 completion。本机只有 Docker，没有真实硬件、真实手机或外部云材料，因此本轮不重复堆 O5 metadata。

近期 PR / review 证据：

- PR #4 将 elevator-assisted delivery 变成必须能力，要求行为链、证据采集和 human-assist 边界进入主线。
- PR #5 扩展硬件边界，要求单目相机 + 2D LiDAR + ToF 安全环，但真实 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry 材料仍缺失。
- 上轮 `2026.05.17_12-13_route-task-handoff-result-intake-bridge/final.md` 已把 `route_task_field_retest_review_result_handoff` 安全接入 `route_task_field_retest_result_intake`，但 result reconciliation 仍只看到普通 result-intake source，不显式保留 handoff-derived lineage，后续 Product/Robot/mobile 复账时难以确认该 result-intake 来自 PR #4 review-result handoff。

## 2. 本轮目标

推进 Objective 2 / Objective 3 的 PR #4 route/elevator field-material 链路：让 `route_task_field_retest_result_reconciliation` 能显式保留并展示 `route_task_field_retest_review_result_handoff -> result_intake -> result_reconciliation` 的安全来源谱系。

本轮仍是 Docker-only `software_proof`，不得宣称真实 route/elevator field pass、HIL、真实手机/browser、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 3. Owner 与并行边界

- Autonomy Algorithm Engineer：PC gate 主责，更新 result reconciliation artifact/summary、focused tests、PC/navigation 文档。
- Robot Platform Engineer：Robot diagnostics 只读消费主责，确保 source lineage metadata-only 暴露且 fail closed。
- User Touchpoint Full-Stack Engineer：mobile/web 只读展示主责，展示 lineage 但不暴露 raw artifact、不改变 Start/Dropoff/Cancel gating。
- Product Manager / OKR Owner：收口 sprint 文档、`OKR.md`、`docs/process/okr_progress_log.md`，并核对 O5 stop rule 与 O2/O3 软件证据边界。

## 4. 风险与红线

- 不读取真实现场文件正文，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
- `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 必须贯穿 PC artifact、Robot diagnostics、mobile fixture/copy 和 sprint closeout。
- 只做围栏验证，不新增大面积测试套件。
