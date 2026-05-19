# Sprint 2026.05.19_12-13 Task Terminal Field Material Intake - Pre Start

## sprint_type: epic

Run time: 2026-05-19 12:00 Asia/Shanghai。

## 1. 启动原因

CEO 本轮要求基于近期 PR 和评审给出具体可执行建议，用 team 继续完成 OKR，功能往前走，测试只围栏，优先推进 OKR 完成度低，同时承认本机只有 Docker，不能把本地 proof 写成真实现场或云端完成度。

live `OKR.md` 4.1 更新时间为 2026-05-19 11:19 Asia/Shanghai。Objective 5 约 68% 是当前最低项，但仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 和真实手机/browser external proof；本机只有 Docker，本轮不能继续用本地 O5 metadata depth 冒充进度。

Objective 1 约 81% 是下一低项，但 `sprints/2026.05.19_10-11_hardware-real-material-escalation-request/final.md` 已完成硬件真实材料升级请求。当前仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001`、真实 `/odom` / `/imu` / `/battery`、operator HIL report，以及 PR #5 要求的 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。重复再做第三个本地硬件 wrapper 不会提高 Objective 1。

GitHub PR #4 已合并，标题为 `Add elevator-assisted delivery capability to agents, registry and OKR`，把 elevator assisted delivery 纳入 agents、registry 和 OKR 主链。GitHub PR #5 已合并，标题为 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline`，进一步要求电梯 assisted delivery 为 MVP 必须能力，并把感知/硬件 baseline 固化为单目摄像头 + 2D LiDAR + ToF 安全环，要求参数化和真实材料。

最近 sprint `sprints/2026.05.19_11-12_task-terminal-completion-mainline/final.md` 已完成 dropoff/cancel terminal action mainline 可观察性，但明确不证明真实 dropoff/cancel completion、route/elevator field pass、Nav2/fixed-route、真实手机、HIL 或 O5 external proof。下一步不应继续停在只读 terminal summary，而应新增一个现场材料回填入口，承接真实 field owner 后续提交的材料。

## 2. 用户价值和产品北极星

用户价值：现场 owner 下一次带回真实 dropoff/cancel terminal materials、route/elevator field materials、real phone/browser evidence 时，Robot diagnostics 和 mobile/web 能用同一 safe `evidence_ref` 明确接收、显示缺口、列出下一步证据要求，并让普通手机用户看到“材料待回填 / 已接受安全引用 / 仍未证明”的边界。

产品北极星保持不变：普通手机用户最终能用低成本 ROS2 自主送垃圾机器人完成“放入垃圾 -> 发车 -> 到站 -> 投放/取消/恢复 -> 复盘”的真实闭环。本轮 `task_terminal_field_material_intake` 只是为后续真实材料进入主链路准备 fail-closed 入口，不证明真实送达。

## 3. OKR 映射

- Objective 5：约 68%，数字最低。本轮不针对 O5 completion，因为没有真实 external proof；不声明公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser 通过。
- Objective 1：约 81%，下一低项。上一轮已完成硬件真实材料升级请求，本轮不继续 O1 hardware wrapper，不新增 WAVE ROVER、UART、2D LiDAR 或 ToF 硬件事实。
- Objective 2：约 99%，本轮主映射。`task_terminal_field_material_intake` 为 dropoff/cancel terminal materials 和电梯 assisted delivery field materials 建立后续回填入口。
- Objective 3：约 99%，本轮主映射。入口必须承接 route/elevator field materials、Nav2/fixed-route evidence fields、route completion signal 的 safe metadata，但不证明真实路线。
- Objective 4：约 99%，本轮主映射。mobile/web 新增只读“现场材料回填入口”panel，解释 missing materials、accepted safe refs、next required evidence 和 evidence boundary。

## 4. KR 拆解或更新

- KR-A：Robot diagnostics 暴露 `robot_diagnostics_task_terminal_field_material_intake_summary`，只消费 sanitized terminal summary/material-intake payload，fail closed，不触发 ACK、commands、Nav2、HIL 或任何 control path。
- KR-B：mobile/web 增加只读“现场材料回填入口”panel，显示 missing materials、accepted safe refs、next required evidence、evidence boundary，并保持 Start Delivery、Confirm Dropoff、Cancel gating 不扩大。
- KR-C：Product closeout 不提高 O5/O1 真实进度，只记录 O2/O3/O4 主链路可回填性；同步 `OKR.md` 和 `docs/process/okr_progress_log.md` 时必须保守。
- KR-D：Autonomy 只读确认 route/elevator/Nav2 evidence fields 与 Objective 3 不冲突，避免把 intake summary 写成 route/fixed-route pass。

## 5. 上轮未完成项和阻塞

- O5 阻塞：仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof。
- O1 阻塞：仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001`、真实 `/odom` / `/imu` / `/battery`、operator HIL report、PR #5 2D LiDAR / ToF 真实材料。
- PR #4 / Objective 2/3 阻塞：仍缺真实 route/elevator field materials、真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、真实 task record、route completion signal、真实 dropoff/cancel completion 和 delivery result。
- O4 阻塞：仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 和真实手机/browser external proof。

## 6. 本轮核心抓手

核心抓手：`task_terminal_field_material_intake`。

它要比 11-12 的只读 `task_terminal_completion_mainline` 往前一步：定义现场材料回填字段、缺材料状态、accepted safe refs、next required evidence、phone-safe material intake copy，并为后续真实材料回填提供同一 safe `evidence_ref` 的主链路。

本轮必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。它不是真实手机、真实电梯、真实 Nav2/fixed-route、HIL、O5 external proof 或 delivery success。

## 7. 责任 Engineer

| Owner | 责任 |
| --- | --- |
| robot-software-engineer | 主责 Robot diagnostics material intake summary；只消费 sanitized payload，输出 `robot_diagnostics_task_terminal_field_material_intake_summary`，fail closed。 |
| full-stack-software-engineer | 主责 mobile/web 只读“现场材料回填入口”panel；显示缺材料和下一步证据，保持所有 primary action gating 不变。 |
| product-okr-owner | 主责实现后 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 保守收口。 |
| autonomy-engineer | 只读咨询 route/elevator/Nav2 evidence fields，确认不与 Objective 3 证据语义冲突。 |
| hardware-engineer | 本轮不写文件；不新增硬件参数或 vendor detail。 |

## 8. 范围边界

允许推进 Docker/local `software_proof` 主链路可回填性。不允许声明或暗示：

- 真实 dropoff completion、真实 cancel completion 或 `delivery_success=true`。
- 真实 route/elevator field pass、真实电梯、真实 Nav2/fixed-route。
- 真实手机、真实 iPhone/Android、production app/browser external proof。
- 真实 WAVE ROVER/UART/HIL 或 PR #5 2D LiDAR / ToF 材料通过。
- Objective 5 external proof 通过。

## 9. 需要创建或更新的 sprint 文档

本轮 Epic sprint 先创建：

- `sprints/2026.05.19_12-13_task-terminal-field-material-intake/pre_start.md`
- `sprints/2026.05.19_12-13_task-terminal-field-material-intake/prd.md`
- `sprints/2026.05.19_12-13_task-terminal-field-material-intake/tech-plan.md`

实现完成后必须继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

实现若改动 Robot 或 mobile/web 行为，必须同步更新对应 `docs/` 文档；Product closeout 必须最终更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，但不得上调 O5 external proof、O1 HIL 或真实 delivery success 完成度。
