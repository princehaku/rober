# Sprint 2026.05.19_23-24 Real Material Followup Escalation Status - Pre Start

## 1. Sprint 类型和启动结论

- sprint_type: epic
- 启动时间：2026-05-19 23:04 Asia/Shanghai。
- 本轮目标：在 `real_material_manifest_template` / `real_material_evidence_intake` 之后，新增 `real_material_followup_escalation_status` 功能计划，让每个 material group 都能显示 owner、due_status、blocked_reason、next_required_evidence、escalation_level、rerun command/status summary。
- 本轮只创建计划三文档：`pre_start.md`、`prd.md`、`tech-plan.md`。不写产品代码，不修改 `OKR.md`，不修改 `docs/process/okr_progress_log.md`。
- 证据边界固定为 `software_proof_docker_real_material_followup_escalation_status_gate`。本轮和后续实现都不得宣称真实外部云、HIL、真实手机、route/elevator field pass、delivery success 或 OKR 百分比提升。

## 2. Live Evidence 和推荐理由

- `OKR.md` 4.1：Objective 5 约 68%，当前最低；Objective 1 约 81%；Objective 2 / Objective 3 / Objective 4 均约 99%。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 等 external proof。当前 Docker-only 主机不能产生这些材料。
- Objective 1 仍缺 WAVE ROVER/UART/HIL、真实串口日志、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF material。
- Objective 2 / Objective 3 / Objective 4 仍缺真实 route/elevator field evidence、真实 Nav2/fixed-route、真实手机/browser、dropoff/cancel completion 和 delivery result。
- GitHub PR #5 review threads：`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，评审要求 mandatory sensor baseline cite `docs/vendor/` sources，当前仍是 `blocked_pending_real_materials`。
- 最近 final：`2026.05.19_20-21_real-material-readiness-board`、`2026.05.19_21-22_real-material-evidence-intake`、`2026.05.19_22-23_real-material-manifest-template` 已完成 readiness / intake / template 三段，但全部是 `software_proof_docker_*`，均未提升 OKR。
- `2026.05.19_22-23_real-material-manifest-template/final.md` 明确写明：下一轮若仍无真实材料，应升级现场材料提供请求，而不是继续堆本地 proof。

## 3. 本轮核心抓手

本轮不是再造一个材料 wrapper，而是把现有材料模板和回填入口推进到 follow-up escalation status：

- 对四类 material group 计算 owner、due_status、blocked_reason、next_required_evidence、escalation_level。
- 输出 rerun command/status summary，让现场 owner 知道应重新运行哪个 intake/template/review 命令或补哪类真实材料。
- Robot diagnostics 只读展示 sanitized status summary，不读取 raw material、不改变控制路径。
- mobile/web 只读展示现场 owner 下一步，保持 Start Delivery、Confirm Dropoff、Cancel fail-closed。
- Autonomy 明确 route/elevator 的真实材料要求，避免将缺材料的状态包装成 field pass。
- Hardware 明确 O1 / PR #5 仍需 `docs/vendor/` source citation 和真实 2D LiDAR / ToF / HIL-entry material。

## 4. 用户价值和产品北极星

产品北极星：普通手机用户最终能让小车可靠送垃圾；现场 owner 和 Engineer 能用同一证据链判断为什么还不能发车、不能上调 OKR、不能关闭 PR thread。

本轮用户价值：

- 现场 owner 不再只看到“缺真实材料”，而是看到谁负责、何时逾期、缺什么、升级到哪一级、该重跑什么命令。
- Product 能把 Objective 5、Objective 1、PR #5、route/elevator、real phone 的阻塞状态转成可追责的 follow-up queue。
- Engineer 能在 Docker-only 环境中继续推进软件可观测性，同时不把本地 proof 误写成真实完成。

## 5. Owner 和启动边界

- Product Manager / OKR Owner：本轮负责规划三文档、推荐理由、OKR 映射、验收口径和后续 owner 拆分。
- Hardware Infra Engineer：后续负责 O1 / PR #5 material follow-up status、vendor/source citation blocker、真实 2D LiDAR / ToF / WAVE ROVER/HIL material 的 owner/due/escalation 字段；执行前必须读取 `docs/vendor/VENDOR_INDEX.md`。
- Autonomy Algorithm Engineer：后续负责 PR #4 route/elevator、Nav2/fixed-route、task record、route completion、dropoff/cancel、delivery_result 的 follow-up status。
- Robot Platform Engineer：后续负责 `robot_diagnostics_real_material_followup_escalation_status_summary` safe alias 和 fail-closed diagnostics consumer。
- User Touchpoint Full-Stack Engineer：后续负责 mobile/web 只读 “真实材料升级状态” panel，不改变主操作 gating。

## 6. 风险、阻塞和证据链缺口

- 最大风险：follow-up status 被误读为真实材料已到位。所有输出必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- O5 仍 blocked 在真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/cutover。
- O1 / PR #5 仍 blocked 在真实 WAVE ROVER/UART/HIL、真实反馈包、2D LiDAR / ToF source/procurement/installation/wiring/power/calibration/HIL-entry；`PRRT_kwDOSWB9286CJ3tX` 仍是 `blocked_pending_real_materials`。
- O2/O3/O4 仍 blocked 在真实 route/elevator/phone evidence，不能把 Robot diagnostics 或 mobile/web 面板计为 field pass。

## 7. 本轮需要创建或更新的 sprint 文档

- 创建 `sprints/2026.05.19_23-24_real-material-followup-escalation-status/pre_start.md`。
- 创建 `sprints/2026.05.19_23-24_real-material-followup-escalation-status/prd.md`。
- 创建 `sprints/2026.05.19_23-24_real-material-followup-escalation-status/tech-plan.md`。
- 后续实现完成后必须继续补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并由 closeout 更新 `OKR.md` 和相关 `docs/`。没有真实材料前不得提高 OKR 百分比。
