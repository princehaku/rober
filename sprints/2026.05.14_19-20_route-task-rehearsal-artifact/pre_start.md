# Sprint 2026.05.14_19-20 Route Task Rehearsal Artifact - Pre Start

## sprint_type: epic

- sprint_type: epic
- 启动时间：2026-05-14 19:20 Asia/Shanghai
- 产品北极星：把固定路线软件状态、任务复盘记录和 evidence crosscheck 对账结果收束成一个可保存、可复核、可移交的 route/task rehearsal artifact，让后续真实 Nav2 / HIL 上车前先有同一 `evidence_ref` 的软件证据闭环。
- 本轮证据边界：`software_proof_docker_route_task_rehearsal_artifact_gate`。
- 重要非声明：本轮不证明真实 Nav2/fixed-route 实跑、不证明 WAVE ROVER 运动、不证明真实串口、不证明 HIL、不证明 dropoff/cancel completion，也不证明真实 delivery success。

## 当前 OKR 排序与切换原因

`OKR.md` 4.1 最新快照显示：

- Objective 5：约 68%，数字最低；缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 材料。
- Objective 1：约 75%；当前 macOS + Docker-only 主机没有真实 WAVE ROVER、串口和 `T=1001` feedback，不能产出真实 `hil_pass`。
- Objective 2：约 77%；仍缺真实 Nav2/fixed-route 运行、同一 `evidence_ref` 的任务复盘、真实送达和失败恢复实测。
- Objective 3：约 77%；仍缺真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据与上车复账。
- Objective 4：约 95%；最近 18-19 sprint 已完成 PWA install prompt evidence export 软件证据，不应继续默认堆 O4 手机材料。

本轮不继续推进 Objective 5 的原因：当前主机没有真实公网入口、TLS、4G/SIM、OSS/CDN 实流量、production DB/queue 或 worker/migration 材料，继续堆本地 O5 metadata depth 不能推动 O5 完成度。  
本轮不继续推进 Objective 1 的原因：当前主机没有真实硬件/串口，不能闭合 WAVE ROVER HIL。  
本轮切到 Objective 2/3 的原因：Docker-only 环境仍可把 fixed-route status、task record 和 `pc-tools/evidence/evidence_crosscheck.py` 对账结果组合为软件层 route/task rehearsal artifact，补齐后续真实路线/任务实跑前的可复盘证据包。

## 最近两轮 blocker 扫描

已扫描最近两轮 sprint final：

- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/final.md`：收口为 O4 `software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`，不是 blocked sprint；同时记录 O5 external proof、Nav2/fixed-route、WAVE ROVER/HIL、delivery success 仍缺。
- `sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/final.md`：收口为 O4 `software_proof_docker_mobile_pwa_install_prompt_event_capture_gate`，不是 blocked sprint；同时记录 O5 external proof、Nav2/fixed-route、WAVE ROVER/HIL、dropoff/cancel completion、delivery success 仍缺。

结论：最近两轮没有以同一根因 blocker 作为 blocked 收口；本轮明确避开 O5 外部证据 blocker 与 O1 硬件 blocker，切到 O2/O3 可执行的软件证据链，不构成第三轮重复消费同一 blocker。

## 本轮核心抓手

把现有三类材料串成一个保存型 artifact：

- fixed-route status：包含 `route_progress`、`software_proof` replay、`failure_code`、`evidence_ref`。
- task record：包含 `final_status`、`nav_results`、`route_progress`、`dropoff_result`、`error_message`、`evidence_ref`。
- evidence crosscheck：由 `pc-tools/evidence/evidence_crosscheck.py` 对 status、replay、task_record、可选 HIL gate 输出进行只读对账。

artifact 必须显式写入 `software_proof_docker_route_task_rehearsal_artifact_gate`、`not_proven`、`production_ready=false` 或等价非生产字段，并保留 HIL gate 缺失时的软件证明边界。

## Owner 与下一步

- Task A `autonomy-engineer`：负责 evidence helper / summary artifact 输出、PC tool 文档和 fixed-route workflow 文档。
- Task B `robot-software-engineer`：负责 task record / behavior fixed-route evidence compatibility 或既有 fenced test，保证 `route_progress` / `evidence_ref` 与 artifact 对齐。
- Task C `product-okr-owner`：实现完成后更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`，只按软件证据边界谨慎调整 O2/O3。

本文件只完成规划；产品代码、测试代码和实现验证必须由后续对应 Engineer 子 agent 执行。
