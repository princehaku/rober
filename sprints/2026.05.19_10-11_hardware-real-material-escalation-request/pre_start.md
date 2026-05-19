# Sprint 2026.05.19_10-11 Hardware Real Material Escalation Request - Pre Start

## sprint_type: epic

Run time: 2026-05-19 10:00 Asia/Shanghai。

## 1. 启动原因

CEO 原始方向是：开始下一轮迭代，根据近期 PR 和评审，建议下一步应深入的 OKR；用 team 继续完成 OKR，重新在功能往前走；本机没有真实硬件，只有 Docker；最后提交并推送。

本轮不继续叠加 route/elevator 本地 wrapper。最近 `2026.05.19_08-09_elevator-field-evidence-material-backfill-review-decision` 和 `2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff` 已经连续消费同一真实 route/elevator material blocker。按同一 blocker 重复消费红线，第三轮不能继续围绕 PR #4 route/elevator material 缺口做同类本地包装；必须切换到新的可执行链路或升级真实材料请求。

live `OKR.md` 4.1 显示 Objective 5 约 68% 是最低项，但当前 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机 external proof，因此本轮不提高 Objective 5，也不消费 O5 blocker。

Objective 1 约 81% 是下一低项，仍缺真实 WAVE ROVER/UART/HIL 和 PR #5 相关 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。PR #5 review closeout 已把两条 mainline docs thread 标成可由 docs close，但 mandatory sensor material 仍是 `blocked_pending_real_materials`。因此本轮方向定为 Objective 1 / Objective 4 的 `hardware_real_material_escalation_request` software-proof chain。

## 2. 用户价值和产品北极星

用户价值：现场 owner 不再只看到“缺真实硬件材料”的散落说明，而是拿到一份跨 PC gate、Robot diagnostics、mobile/web 的只读升级请求，明确下一步必须提供哪些真实 2D LiDAR / ToF / WAVE ROVER / UART / HIL 材料，避免普通用户和工程同学把 Docker 软件证明误当成实机验收。

产品北极星保持不变：低成本 ROS2 自主送垃圾机器人必须先建立可信硬件边界和可复盘证据链，再推进真实路线、电梯、手机和云端验证。本轮只把真实材料请求产品化，不证明真实硬件。

## 3. OKR 映射

- Objective 5：约 68%，数字最低。本轮明确不提高 O5，因为没有真实 external proof；不把 hardware escalation request 写成云中转、OSS/CDN、4G 或 production proof。
- Objective 1：约 81%，本轮主目标。把 WAVE ROVER/UART/HIL 与 PR #5 2D LiDAR / ToF 真实材料缺口转成可执行升级请求链路，但仍保持 `software_proof`、`not_proven`。
- Objective 4：约 99%，本轮辅助目标。mobile/web 只读展示材料请求与安全边界，帮助普通手机用户/现场 owner 理解缺口；不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- Objective 2 / Objective 3：约 99%，本轮不继续消费 PR #4 route/elevator material blocker；PR #4 真实电梯/路线材料仍是独立缺口。

## 4. 上轮未完成项和阻塞

- O5 仍缺真实 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover。
- O1 仍缺真实 WAVE ROVER `/dev/tty*`、真实 UART、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、operator HIL report。
- PR #5 mandatory sensor baseline 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- PR #4 route/elevator field materials 已连续两轮被本地 software-proof wrapper 消费，本轮必须停止第三次同源消费。

## 5. 本轮核心抓手

核心抓手：`hardware_real_material_escalation_request`。

本轮要把“真实材料缺口”变成一个 fail-closed、phone-safe、diagnostics-safe 的升级请求链路：

1. Hardware PC gate 产出 `hardware_real_material_escalation_request` artifact / summary。
2. Robot diagnostics 暴露 safe alias，只读展示 summary，不触发硬件、串口或运动。
3. mobile/web 新增只读 panel，说明缺哪些材料、谁提供、下一步怎么补，不改变主操作按钮 gating。
4. Product closeout 更新 sprint 留档、OKR 证据边界和剩余风险。

## 6. 责任 Engineer

| Owner | 责任 |
| --- | --- |
| hardware-engineer | 主责 PC gate、真实材料字段、vendor/source 边界和硬件证据请求；必须引用 `docs/vendor/VENDOR_INDEX.md`。 |
| robot-software-engineer | 主责 `operator_gateway_diagnostics.py` safe alias 和 diagnostics contract，保证只读、fail-closed。 |
| full-stack-software-engineer | 主责 mobile/web 只读 panel、fixtures、targeted tests 和 `docs/product/mobile_user_flow.md` 同步。 |
| product-okr-owner | 主责 sprint closeout、OKR evidence boundary、docs/process progress log 和最终 `OKR.md` 进展更新。 |
| autonomy-engineer | 本轮无写范围；PR #4 route/elevator field pass 缺口保持后续独立材料，不在本轮继续包装。 |

## 7. 范围边界

本轮允许做 software-proof chain，不允许声明或暗示：

- 真实 HIL 通过。
- 真实 WAVE ROVER/UART 通过。
- 真实 2D LiDAR / ToF 已采购、安装、接线、供电、标定或进入 HIL。
- 真实手机/iPhone/Android 设备通过。
- PR #4 route/elevator field pass 通过。
- Objective 5 external proof 通过。
- delivery success、dropoff completion 或 cancel completion。

所有输出必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 8. 需要创建或更新的 sprint 文档

本轮 Epic sprint 先创建：

- `sprints/2026.05.19_10-11_hardware-real-material-escalation-request/pre_start.md`
- `sprints/2026.05.19_10-11_hardware-real-material-escalation-request/prd.md`
- `sprints/2026.05.19_10-11_hardware-real-material-escalation-request/tech-plan.md`

实现完成后必须继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

若功能或接口文档被修改，对应 `docs/` 文档必须同步更新；最终 Product closeout 再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
