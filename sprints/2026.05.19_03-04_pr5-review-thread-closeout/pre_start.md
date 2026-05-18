# Sprint 2026.05.19_03-04 PR5 Review Thread Closeout - Pre Start

## sprint_type: epic

Run time: 2026-05-19 03:04 Asia/Shanghai

## 用户价值和产品北极星

用户价值：CEO 和现场 owner 需要知道 PR #5 的 review thread 哪些已经能靠 mainline 文档证据关闭，哪些仍必须等真实 2D LiDAR / ToF 材料回填。当前如果只靠口头判断，容易把 `docs/product/production_hardware_boundary.md` 已修复的边界和仍缺的采购、安装、接线、标定、HIL-entry 混在一起。

产品北极星：普通手机用户最终能使用低成本 ROS2 trash delivery robot，但产品闭环必须建立在可追溯硬件边界和 review closeout 证据上。本轮只做 `pr5_review_thread_closeout` 的 `software_proof` gate，不声明真实硬件、真实采购、HIL、field pass 或 delivery success。

## 开工依据

- Live `OKR.md` 4.1 更新时间为 2026-05-19 02:11，最新 sprint 是 `sprints/2026.05.19_02-03_elevator-feedback-task-record-trace`。
- Objective 5 约 68%，数字最低，但仍缺真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和 external proof；本机只有 Docker，继续本地 O5 wrapper 不能推进 O5 completion。
- Objective 1 约 81%，次低且与 PR #5 直接相关；仍缺 WAVE ROVER/UART/HIL、真实串口反馈、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`，以及 PR #5 2D LiDAR / ToF 的真实 SKU/source、receipt、采购、安装、接线、电源、标定、HIL-entry 和 field evidence。
- Objective 2 / Objective 3 / Objective 4 约 99%，但 PR #4 仍缺真实电梯门状态、楼层确认、人工协助、Nav2/fixed-route runtime log、真实 task_record/completion signal、dropoff/cancel completion 和 delivery result。
- 最新 `02-03` final 明确下一步需要真实材料，而不是继续本地 wrapper；其中 PR #5 的真实 2D LiDAR / ToF 材料被列为独立缺口。
- GitHub PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 仍有 3 条 unresolved review thread：P1 `docs/product/production_hardware_boundary.md` default hardware set 与 mandatory sensor baseline 矛盾；P2 `OKR.md` lowest objective narrative 与 table 不一致；P2 mandatory sensor assumptions 缺 `docs/vendor/` citation。
- PR #4 没有 review comments，但其 route/elevator field materials 仍是未回填证据链，必须继续和 PR #5 硬件 closeout 区分。
- 当前 mainline `docs/product/production_hardware_boundary.md` 已把 default hardware set 与 target LiDAR/ToF pending baseline 分离，并写明 vendor/source attribution boundary；但 GitHub threads 未收口，现场 owner 缺 repo-local evidence artifact 判断每条 thread 是 `ready_to_close_on_mainline_docs`、`blocked_pending_real_materials` 还是 `still_open_missing_current_evidence`。
- 硬件事实入口已按 AGENTS 要求核对 `docs/vendor/VENDOR_INDEX.md`；本 sprint 不新增引脚、电压、UART 设备、波特率、JSON 指令、速度映射、反馈协议或机械尺寸假设。

## 本轮核心抓手

实现 `pr5_review_thread_closeout` software-proof gate 的规划：把 PR #5 的 unresolved review threads、当前 mainline 文档、`docs/vendor/VENDOR_INDEX.md` 和 `OKR.md` 组合为一份 closeout artifact/summary。每条 thread 输出 closeout decision、证据引用、仍缺材料和 owner handoff，让 Product 能决定是否关闭 thread 或继续保持 open。

本轮必须保持：

- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- metadata-only / Docker-only

本轮不得声明：

- 真实 2D LiDAR 或 ToF 已采购、安装、接线、供电、标定或 HIL 通过
- 真实 WAVE ROVER/UART/HIL
- 真实 route/elevator field pass
- 真实手机/browser 或 O5 external proof
- delivery success

## Sprint 归属和 owner

本轮是跨 owner Epic sprint。进入实现阶段时必须并行启动 Hardware、Robot、Full-Stack worker；Product 负责规划和最终 closeout，不写产品代码。

| Owner | 责任 | 范围边界 |
| --- | --- | --- |
| product-okr-owner | 本 planning 文档、OKR 映射、验收口径、实现后 OKR 和 progress log 收口 | 本阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md` |
| hardware-engineer | `pr5_review_thread_closeout_gate`、PR #5 thread summary / fixture、安全 evidence artifact、focused test | 不改硬件配置，不声明真实材料，不猜测 vendor 事实 |
| robot-software-engineer | operator diagnostics 增加 `robot_diagnostics_pr5_review_thread_closeout_summary` safe alias | 只读消费 summary，不启用控制或 delivery action |
| full-stack-software-engineer | mobile/web 增加只读 PR #5 review closeout panel 和 fixture | 不触发 Start/Confirm/Cancel，不主动拉取 diagnostics |
| autonomy-engineer | 本轮不写代码；PR #4 route/elevator field evidence 保持后续独立缺口 | 不把 PR #5 closeout gate 写成 route/elevator pass |

## Blocker 扫描

- O5 external proof blocker：真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和 external proof 均缺；本轮不消费 O5 blocker。
- O1 real hardware blocker：本机无真实 WAVE ROVER/UART/HIL，也无真实 2D LiDAR / ToF materials；本轮只做 review closeout decision，不把 blocker 写成已解决。
- PR #5 review closeout blocker：GitHub thread 未收口，且现场 owner 缺 repo-local evidence artifact。本轮正面推进这个可在 Docker-only 环境完成的 metadata gate。
- PR #4 field evidence blocker：PR #4 无 review comments，但真实 route/elevator materials 仍缺；本轮只在 summary 中保留为独立 `not_proven`，不混入 PR #5 thread closeout。

## 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 本阶段不得创建：`tech-done.md`、`side2side_check.md`、`final.md`。
- 实现完成后：worker 更新 `tech-done.md`；Product 验收后更新 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
