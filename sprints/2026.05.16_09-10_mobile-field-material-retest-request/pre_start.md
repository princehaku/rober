# Sprint 2026.05.16_09-10 Mobile Field Material Retest Request - Pre Start

sprint_type: epic

## 1. 开工声明

本轮为 planning-only Epic sprint。当前只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，不做实现代码、不改测试、不改 `OKR.md`、不更新 closeout 文档；本阶段只提交/推送 planning 文档，不提交实现代码或 OKR/closeout 更新。

本轮后续实现必须并行派发 3 个 Engineer worker：

- Autonomy：负责 route/elevator field retest request gate。
- Robot：负责 diagnostics metadata-only consumer。
- Full-stack：负责 `mobile/web` 只读 retest request panel。

Product closeout 后置，只有在 A/B/C worker 返回实际改动和验证结果后，才允许更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和相关 `docs/`。

## 2. 为什么从 Objective 5 / Objective 1 切到 Objective 2 / Objective 3

当前 `OKR.md` 4.1 显示 Objective 5 约 66%，是数字最低的 Objective。但 Objective 5 的剩余进展需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部证据；本机只有docker，无法补这些真实外部材料。继续堆本地 O5 metadata 会重复消费同一 blocker，不能形成真实云/4G/OSS/CDN/DB/queue product proof。

Objective 1 约 73%，也仍缺真实 WAVE ROVER、UART、Orange Pi 串口、`T=1001` feedback、HIL 和真实底盘样本。本机没有真实硬件，不能 claim `hil_pass`，也不能把 Docker/local proof 写成真实 WAVE ROVER 或 UART 证明。

因此本轮切到 Objective 2 / Objective 3 的可执行链路：把上一轮 `mobile_field_material_review_decision` 输出的 blockers / next-required-evidence / owner handoff 转成更可执行的 route/elevator field retest request artifact，并让 Robot diagnostics 和 mobile/web 以 metadata-only / 只读方式消费。Objective 4 只作为手机用户触点支撑，Objective 1 / Objective 5 本轮不进入上调范围。

## 3. 上轮 08-09 评审证据

上一轮 `sprints/2026.05.16_08-09_mobile-field-material-review-decision/final.md` 收口为 `software_proof_docker_mobile_field_material_review_decision_gate`，已完成：

- PC gate 输出 `mobile_field_material_review_decision` artifact/summary。
- Robot diagnostics 以 metadata-only 方式消费 review decision。
- `mobile/web` 以只读 panel 展示 review decision、blocker、next-required-evidence、owner handoff、safe `evidence_ref`、same-evidence-ref、`not_proven` 和 boundary。
- `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 在 PC gate、Robot diagnostics、mobile panel 和 closeout 文档中一致。

上一轮也明确不证明真实手机/PWA、真实 route/elevator field pass、真实 Nav2/fixed-route、真实路线采集、真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue。

## 4. 本轮目标

把 review decision 继续推进成 retest request：

- artifact/schema：`trashbot.mobile_field_material_retest_request.v1`
- summary/schema：`trashbot.mobile_field_material_retest_request_summary.v1`
- evidence boundary：`software_proof_docker_mobile_field_material_retest_request_gate`
- 核心字段：source review decision、blockers、next_required_evidence、retest_request、route/elevator material checklist、owner handoff、safe `evidence_ref`、same_evidence_ref_required/status、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

本轮规划目标不是宣称现场复测已完成，而是把“评审发现缺口”转换成“现场人员下一次 route/elevator field retest 该带什么、采什么、交给谁”的可执行请求。

## 5. 本轮不做

- 不修改代码、测试、fixtures、docs product/interface/navigation 或 `OKR.md`。
- 本阶段只提交/推送 planning 文档，不提交实现代码、测试、`OKR.md` 或 closeout 更新。
- 不声称真实手机、真实 route/elevator、真实 Nav2/fixed-route、真实 dropoff/cancel、真实 delivery success、真实 WAVE ROVER/UART/HIL 或 Objective 5 external proof。
- 不启用 Start Delivery、Confirm Dropoff、Cancel，不改变 `command_safety` 和主操作 gating。
- 不读取或引用 raw artifact、raw ROS topic、`/cmd_vel`、串口、波特率、WAVE ROVER 参数、credentials、DB/queue URL、OSS AK/SK、local path、traceback、checksum 或 complete artifact 到手机 copy。

## 6. 风险与证据缺口

- O5 外部证据仍未补齐：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- O1 / HIL 证据仍未补齐：真实 WAVE ROVER、UART、Orange Pi 串口、`T=1001` feedback、真实 `/odom` / `/imu/data` / `/battery` 样本。
- O2 / O3 仍缺真实 route/elevator field retest：真实电梯门状态、真实目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` task record/completion signal、dropoff/cancel completion 或 delivery result。
- O4 手机证据仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。

## 7. Planning 验收

本阶段只验收三份 planning 文件存在、包含 Objective / review decision / retest request / software proof / not_proven / fail-closed 边界关键词，并通过 scoped diff whitespace 检查。后续实现验收命令写入 `tech-plan.md`，但本阶段不运行实现测试。
