# Sprint 2026.05.19_16-17 Task Terminal Field Material Review Decision - Pre Start

## sprint_type: epic

Run window: 2026-05-19 16:00-17:00 Asia/Shanghai.

## 1. 启动背景

本轮从 `task_terminal_field_material_intake` 继续推进到 `task_terminal_field_material_review_decision`。上一轮 `sprints/2026.05.19_12-13_task-terminal-field-material-intake/final.md` 已完成 Robot diagnostics safe alias 和 mobile/web 只读“现场材料回填入口”，但只证明 Docker/local `software_proof` 的回填入口存在，不证明真实 dropoff/cancel completion、真实 route/elevator field pass、真实 Nav2/fixed-route、真实手机/browser、WAVE ROVER/UART/HIL 或 delivery success。

最新 `sprints/2026.05.19_15-16_pr5-github-thread-resolution/final.md` 已把 PR #5 两个 docs-closeout review threads resolved，并修复 `pr5_review_thread_closeout_gate.py --output-dir` 兼容性；剩余 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，根因是缺真实 2D LiDAR / ToF vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

## 2. OKR 切换原因

- `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 68%。它的下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实外部手机/browser 证据；当前 Docker-only 主机无法产生这些材料，继续做本地 O5 wrapper 会重复消费同一 blocker。
- Objective 1 约 81%，但 PR #5 剩余 thread `PRRT_kwDOSWB9286CJ3tX` 只能由真实 2D LiDAR / ToF SKU/source、receipt、采购、安装、接线、电源、标定和 HIL-entry 材料解锁。本轮不得关闭该 thread，也不得把 PR #5 docs-closeout 写成 O1 进展。
- PR #4 已把 elevator-assisted delivery 纳入主链路，PR #5 review comments 又要求硬件 baseline 和 vendor/source 证据一致。当前不重复 O5/O1 blocker 的可执行抓手，是把已回填或缺失的 terminal field materials 转成只读 review decision，指导现场 owner 下一步补什么材料、由谁接手、何时可以 rerun。

## 3. 本轮目标

创建并执行 `task_terminal_field_material_review_decision` 能力：把 terminal field material intake 中的 returned/missing materials 转成 `accepted`、`missing`、`rejected`、`owner_handoff`、`next_required_evidence` 和 rerun guidance。

本轮边界固定为 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。任何 ready/accepted wording 只能表示 review decision 已整理清楚，不表示真实路线、电梯、投放、取消、手机或硬件通过。

## 4. Owner 和并行策略

- `robot-software-engineer`：负责 Robot diagnostics safe alias 和 fail-closed summary contract。
- `full-stack-software-engineer`：负责 mobile/web 只读 review decision panel 和 phone-safe copy/export。
- `autonomy-engineer`：负责 route/elevator/Nav2 review decision gate 或咨询验证，确保 Objective 3 证据字段不被写成真实 field pass。
- `product-okr-owner`：负责本轮验收口径、OKR 边界和收口留档；实现完成后再更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

实现阶段必须并行派发 Robot、Full-Stack、Autonomy 三个 worker；Product closeout 必须等三方验证结果返回后再写收口文档。

## 5. 验收口径

- 必须存在 `task_terminal_field_material_review_decision` 的 artifact / summary / Robot diagnostics / mobile safe display 口径。
- 缺输入、unsupported schema、unsafe copy、raw artifact、local path、credential、checksum、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER detail、success wording、HIL/pass wording、route/elevator field-pass wording、`delivery_success=true`、`primary_actions_enabled=true` 或 `safe_to_control=true` 必须 fail closed。
- mobile/web 不新增 ACK、cursor、diagnostics fetch、Start Delivery、Confirm Dropoff、Cancel、review route、handoff route、Nav2、HIL 或 robot command。
- docs 必须同步更新 `docs/interfaces/`、`docs/product/mobile_user_flow.md` 和 `pc-tools/README.md` 的相关段落；新增代码技术注释必须为中文，并解释为什么 fail closed。

## 6. 剩余风险

- 本轮不产生真实外部云证据，不提高 Objective 5。
- 本轮不产生真实 WAVE ROVER/UART/HIL 或 2D LiDAR / ToF 材料，不提高 Objective 1，也不关闭 `PRRT_kwDOSWB9286CJ3tX`。
- 本轮不证明真实 dropoff/cancel completion、真实 route/elevator field pass、真实 Nav2/fixed-route、真实手机/browser、真实投放或 delivery success。
