# Pre Start - PR5 mandatory sensor material owner-response reviewer ACK intake

- sprint_type: epic
- sprint: `2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake`
- planning time: 2026-05-24 12:08 Asia/Shanghai
- Product owner: `product-okr-owner`
- implementation owners: `hardware-engineer`, `robot-software-engineer`, `full-stack-software-engineer`
- target capability: `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`
- proof boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate`
- OKR decision expectation: no OKR percentage lift

## 用户价值和产品北极星

本轮用户价值不是证明真实 2D LiDAR / ToF 已采购、安装或通过 HIL，而是把 PR #5 mandatory sensor material 的 owner-response review handoff 之后的 reviewer ACK 回执安全接入三条用户可见链路：PC gate、Robot diagnostics safe alias、手机只读 panel。这样 support、hardware owner 和 reviewer 可以看到同一个 `PRRT_kwDOSWB9286CJ3tX`、同一个 `hardware_material_pending`、同一个 next evidence list，并且不会把软件证据误读成真实硬件或交付成功。

产品北极星保持：普通手机用户只看到安全、可解释、不可误操作的状态；真实硬件材料缺失时，主操作必须 fail closed。

## 证据来源

- `AGENTS.md`：要求所有复杂任务进入 sprint 留档，Epic sprint 必须有 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`。
- `OKR.md` 4.1：Objective 5 当前最低，约 68%；Objective 1 约 81%，仍 blocked on PR #5 material thread 和真实硬件/HIL 材料。
- 最新 sprint final / tech-done：`sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/` 已完成 `pr5_mandatory_sensor_material_owner_response_review_handoff`，边界为 `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`，no OKR percentage lift。
- GitHub PR evidence：PR #5 closed/merged；review threads `PRRT_kwDOSWB9286CJ3tQ`、`PRRT_kwDOSWB9286CJ3tU` resolved；thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`。PR #7 open，review threads empty。
- Automation memory：上一轮 `81dfeb1 Add PR5 sensor review handoff gate` 已 push，`origin/master` aligned；boundary 保留 `source=software_proof`、`hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 上轮未完成项和本轮转入原因

上一轮把 owner-response review decision 转成 owner/support/reviewer handoff，但真实材料仍缺失：

- reviewed 2D LiDAR SKU/source/receipt or purchase material
- reviewed ToF SKU/source/channel-count material
- mounting, wiring, power budget and calibration plan
- real HIL-entry package
- WAVE ROVER powered bench/UART/HIL logs
- reviewer resolution for `PRRT_kwDOSWB9286CJ3tX`

因为本机是 Docker-only 且没有真实硬件，本轮不能提高 Objective 1 或 Objective 5 的百分比。为了继续功能往前走，本轮只推进 PR #5 mandatory sensor material governance chain 的下一条可执行 rung：`pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中完成度最低的是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接推进 Objective 5。
3. 具体理由：Objective 5 当前真实外部材料缺失，包括 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof 和 verified terminal result；最近多轮 O5 local Docker wrappers 都没有 OKR lift。继续叠 O5 local-only wrapper 只会重复消费 blocker。本轮选择 Objective 1 的 PR #5 reviewer evidence chain 下一条可执行 governance rung，并明确不提高 OKR 百分比。

## 本轮核心抓手

三路并行推进，同一 proof boundary、同一 PR thread、同一 false-state flags：

| Track | Owner | 核心抓手 |
| --- | --- | --- |
| Hardware PC gate | `hardware-engineer` | 从上一轮 owner-response review handoff summary 生成 reviewer ACK intake artifact/summary，分类 reviewer ACK missing/accepted/reassignment/blocked，并保留真实材料缺口。 |
| Robot diagnostics safe alias | `robot-software-engineer` | 将 reviewer ACK intake summary 暴露为 read-only diagnostics safe alias，并接入 `/api/status`、`/api/diagnostics` 或现有 remote relay safe surface。 |
| Full-Stack mobile read-only panel | `full-stack-software-engineer` | 在 `mobile/web` first-screen 增加只读 reviewer ACK intake panel，展示 PR #5 thread、ack status、next evidence 和 false-state flags；主操作继续 disabled。 |

Product closeout 后续只做验收和留档：更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，并保持 no OKR percentage lift。

## 需要做什么

1. Hardware：新增 dependency-free PC gate 与 focused tests，输入上一轮 safe handoff summary，输出 `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake` safe summary。
2. Robot：新增 diagnostics builder / safe alias / relay exposure，确保只暴露 sanitized fields 和 false-state flags。
3. Full-Stack：新增 read-only mobile panel、fixture、focused tests 和 `docs/product/mobile_user_flow.md` 同步说明。
4. Product：验收 worker output 后更新 closeout docs、OKR snapshot 和 progress log；如真实材料仍缺失，继续写明 no OKR percentage lift。

## 风险、阻塞和证据链缺口

- 当前主机 Docker-only、没有真实硬件；本轮不是 HIL、不是 WAVE ROVER/UART proof、不是 real LiDAR/ToF installed proof。
- `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；本轮不可请求或暗示 PR #5 resolved。
- 本轮不是 true phone/browser proof、不是 O5 external proof、不是 public HTTPS/TLS、不是 4G/SIM、不是 OSS/CDN live traffic、不是 production DB/queue、不是 worker/cutover。
- 本轮不是 route/elevator field pass、不是 Nav2/fixed-route runtime pass、不是 verified terminal result、不是 delivery success。
- 所有 surfaces 必须保留：`source=software_proof`、`hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 本轮需要创建或后续更新的 sprint 文档

- 已创建 planning docs：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实施完成后必须更新：`tech-done.md`。
- 验收完成后必须更新：`side2side_check.md`。
- 收口完成后必须更新：`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
