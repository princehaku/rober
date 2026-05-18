# Sprint 2026.05.19_03-04 PR5 Review Thread Closeout - PRD

## 用户价值和产品北极星

用户价值：PR #5 的 review feedback 已经从“代码能不能跑”转成“硬件边界和证据是否可关闭”。现场 owner 需要一份 repo-local、可复跑、可被 Robot diagnostics 和 mobile/web 只读展示的 closeout summary，避免在 GitHub thread、`OKR.md`、`production_hardware_boundary.md`、`docs/vendor/VENDOR_INDEX.md` 之间人工对照。

产品北极星：低成本 trash delivery robot 不能靠模糊硬件假设推进。PR #5 closeout 必须告诉团队：哪些 review thread 可基于 mainline 文档关闭，哪些仍因真实 2D LiDAR / ToF 材料缺失保持 open。该能力服务于可信硬件边界，不服务于宣称硬件完成。

## OKR 映射

- Objective 1：主要关联。PR #5 的 mandatory sensor baseline、vendor citation 和 2D LiDAR / ToF evidence gap 属于可信底盘/硬件边界的可追溯性工作。本轮只提升 review closeout 可判定性，不提升真实 HIL 或硬件完成度。
- Objective 4：次要关联。量产硬件约束和手机端可读状态需要知道默认 hardware set 与 target sensor baseline 的区别；mobile/web 只读 panel 只展示 closeout decision 和缺口。
- Objective 5：不推进。O5 约 68%，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。本轮不得把 review closeout 写成云 proof。
- Objective 2 / Objective 3：不推进。PR #4 无 review comments，但 route/elevator field materials 仍缺。本轮不证明真实电梯、真实 Nav2/fixed-route、真实 completion signal 或 delivery result。

## KR 拆解或更新

1. Objective 1 KR evidence hygiene：新增 PR #5 review thread closeout gate，明确每条 review thread 的 current evidence、decision、remaining material gap 和 owner handoff。
2. Objective 4 KR3 / KR9：量产硬件边界展示必须区分 default hardware set、target 2D LiDAR / ToF baseline、vendor-source coverage 和 pending real materials。
3. Product closeout KR：实现完成后，Product 只能在 `OKR.md` 里记录 closeout decision gate 的 software-proof 进展；不得提高真实硬件、HIL、field pass 或 delivery success 百分比。
4. PR #5 GitHub closeout support：输出足够具体的 `ready_to_close_on_mainline_docs` / `blocked_pending_real_materials` / `still_open_missing_current_evidence`，让 reviewer 能逐条判断 thread 是否关闭。

## 本轮核心抓手

核心抓手是 `pr5_review_thread_closeout` metadata gate：

- 输入：PR #5 unresolved review thread summary、`docs/product/production_hardware_boundary.md`、`docs/vendor/VENDOR_INDEX.md`、`OKR.md`。
- 判断：逐条映射 thread 到 mainline 证据。
- 输出：artifact 和 sanitized summary，包含 thread id/label、severity、decision、evidence_refs、missing_real_materials、owner_handoff、rerun_commands。
- 消费：Robot diagnostics 和 mobile/web 只读展示 same summary。
- 边界：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 需要做什么

### Hardware Engineer

- 新增或更新 `pc-tools/evidence/pr5_review_thread_closeout_gate.py`。
- 新增 focused test，覆盖三类决策：
  - P1 hardware boundary contradiction：若 `production_hardware_boundary.md` 已分离 default hardware set 与 target LiDAR/ToF pending baseline，并有 vendor/source boundary，则输出 `ready_to_close_on_mainline_docs`；若缺当前证据则输出 `still_open_missing_current_evidence`。
  - P2 OKR lowest objective narrative mismatch：若 `OKR.md` 4.1 表格与第 6 节下一步 narrative 一致说明 O5 最低但外部 proof blocked、O1 次低且 PR #5 materials pending，则输出 `ready_to_close_on_mainline_docs`；若 narrative 与 table 冲突则输出 `still_open_missing_current_evidence`。
  - P2 mandatory sensor assumptions缺 vendor citation：若 `docs/vendor/VENDOR_INDEX.md` 只证明 Orange Pi / WAVE ROVER / UART / camera vendor coverage，且 `production_hardware_boundary.md` 明确 2D LiDAR / ToF 是 pending target material，则输出 `blocked_pending_real_materials` 或 `ready_to_close_on_mainline_docs`，具体取决于 thread 是否只要求 citation 边界还是要求真实 SKU/source。
- artifact 必须嵌入安全 thread summary 或读取安全 fixture，不读取 GitHub token、raw review body、credential、完整本机路径或未脱敏日志。
- summary 必须包含 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### Robot Platform Engineer

- 在 operator diagnostics 增加 `robot_diagnostics_pr5_review_thread_closeout_summary` safe alias。
- 只读消费 Hardware gate summary，暴露 thread decision、missing materials、owner handoff 和 rerun command。
- 不启用 task action、Start Delivery、Confirm Dropoff、Cancel、ACK、cursor 或 `/cmd_vel`。
- 对缺失 summary、unsupported schema、unsafe copy、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` fail closed。

### Full-Stack Engineer

- 在 `mobile/web` 增加只读 PR #5 review closeout panel 和 fixture。
- 展示每条 thread 的 decision、当前证据、缺失真实材料和下一步 owner，不暴露 raw JSON、GitHub token、ROS topic、serial path、credentials 或 traceback。
- 不触发 Start Delivery、Confirm Dropoff、Cancel，也不新增主动 diagnostics fetch；只消费现有 fixture/status 中的 safe summary。
- 覆盖 safe summary、missing summary、blocked pending materials、ready-to-close 和 unsupported schema 的 targeted validation。

### Product OKR Owner

- 实现完成后更新 `OKR.md`、`docs/process/okr_progress_log.md`、`side2side_check.md` 和 `final.md`。
- closeout 文案必须说明本 sprint 只让 PR #5 thread decision 可复跑，不提高真实硬件、HIL、field pass、O5 external proof 或 delivery success。

## 优先级和验收口径

P0：

- 三条 PR #5 unresolved review thread 均有明确 decision。
- artifact / summary 引用 `docs/product/production_hardware_boundary.md`、`docs/vendor/VENDOR_INDEX.md` 和 `OKR.md` 的当前 mainline evidence。
- Robot diagnostics 和 mobile/web 都只读展示同一 safe summary。
- 所有输出保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

P1：

- 决策可解释：每条 thread 写明 evidence refs、missing real materials、owner handoff、rerun commands。
- unsafe copy fail closed：不得泄露 GitHub token、credential、完整本机路径、raw artifact、raw review body、serial device 或 traceback。
- docs/product 或 docs/interfaces 同步说明 gate 边界和 closeout contract。

不验收：

- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`。
- 真实 route/elevator field pass、Nav2/fixed-route runtime、completion signal、dropoff/cancel completion、delivery result。
- Objective 5 real HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。

## 风险、阻塞和需要补齐的证据链

- 风险：`ready_to_close_on_mainline_docs` 被误读成真实硬件材料已补齐。缓解：summary 同时列出 `not_proven` 和 `missing_real_materials`。
- 风险：GitHub review thread 文案漂移。缓解：gate 使用安全 thread summary / fixture，并在 `owner_handoff` 中要求关闭 thread 前核对 GitHub 当前 thread 状态。
- 风险：Robot/mobile copy 暗示可以开始真实控制。缓解：所有 consumers 只读，且 `primary_actions_enabled=false` 必须保持布尔 false。
- 阻塞：真实 2D LiDAR / ToF materials 仍缺，不能关闭“要求真实 SKU/source/material”的 thread。
- 阻塞：本机只有 Docker，无真实 WAVE ROVER/UART/HIL、真实手机/browser、真实云外部 proof。

## 需要创建或更新的 sprint 文档

本 planning 阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。实现完成后才创建或更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
