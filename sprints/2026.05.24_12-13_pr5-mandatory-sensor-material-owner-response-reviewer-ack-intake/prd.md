# PRD - PR5 mandatory sensor material owner-response reviewer ACK intake

- sprint_type: epic
- sprint: `2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake`
- target capability: `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`
- proof boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate`
- Product owner: `product-okr-owner`
- implementation owners: `robot-hardware-engineer`, `robot-software-engineer`, `full-stack-software-engineer`

## 1. 用户价值和产品北极星

当 PR #5 的 mandatory sensor material thread 仍 unresolved 时，普通手机用户、support reviewer 和 hardware owner 都需要看到同一个安全状态：材料仍 pending、机器人不能控制、delivery 没有成功、下一步必须补真实硬件材料。本轮把上一轮 owner-response review handoff 转成 reviewer ACK intake，让 reviewer ACK 的缺失、接受、改派或 blocked 状态有统一入口，而不是散落在聊天、PR comment 或 raw artifact 里。

北极星：低成本 ROS2 垃圾投递机器人必须让非技术用户通过手机看到安全、简洁、可解释的状态；当真实硬件材料缺失时，任何 UI/API/diagnostics 都不能暴露控制入口或成功暗示。

## 2. OKR 映射

| Objective | 本轮关系 | 进度判断 |
| --- | --- | --- |
| Objective 1：硬件协议可信底盘 | 本轮继续 PR #5 mandatory sensor material evidence chain，但只做 reviewer ACK intake software proof。 | 保持约 81%，no OKR percentage lift。 |
| Objective 4：手机用户体验与低成本量产边界 | 本轮会新增或刷新 `mobile/web` read-only reviewer ACK intake panel。 | 保持约 99%，not true phone/browser proof。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 当前最低约 68%，但本轮不直接推进。 | 保持约 68%，因为真实 O5 external proof 缺失且 recent O5 local wrappers 无 OKR lift。 |

本轮明确不更新 OKR 百分比。若 closeout 发现只有 local software proof，`OKR.md` 必须保持 conservative snapshot。

## 3. KR 拆解或更新

| KR | Owner | 用户价值 | 验收口径 |
| --- | --- | --- | --- |
| KR-A Hardware reviewer ACK intake gate | `robot-hardware-engineer` | reviewer ACK 状态能从上一轮 handoff 被安全接入和分类。 | PC gate 输出 artifact/summary，包含 `PRRT_kwDOSWB9286CJ3tX`、`hardware_material_pending`、proof boundary、next evidence 和 false-state flags；focused unit tests pass。 |
| KR-B Robot diagnostics safe alias | `robot-software-engineer` | Robot/API 只暴露可给手机和 support 使用的安全摘要。 | `/api/status`、`/api/diagnostics` 或既有 relay safe surface 能提供 read-only safe alias；无 raw UART、serial、credential、ROS control topic、GitHub mutation 或 robot command side effects。 |
| KR-C Full-Stack read-only panel | `full-stack-software-engineer` | 普通手机用户和 support 能看到 reviewer ACK intake 状态，但不能误操作。 | `mobile/web` first-screen panel 展示 ack status、thread、pending materials、next evidence 和 safe copy；Start Delivery / Confirm Dropoff / Cancel 保持 disabled。 |
| KR-D Product closeout | `product-okr-owner` | sprint 证据可复账，OKR 不被软件证明虚增。 | `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 保守更新；明确 no OKR percentage lift。 |

## 4. 本轮核心抓手

核心抓手是 `reviewer_ack_intake`，不是真实材料验收。所有实现必须围绕同一状态机表达：

- input：上一轮 `pr5_mandatory_sensor_material_owner_response_review_handoff` safe summary。
- status：reviewer ACK accepted / missing / reassignment-needed / blocked。
- evidence：仍指向 PR #5 thread `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`。
- output：PC artifact、Robot diagnostics safe alias、mobile read-only panel 三者使用同一 proof boundary。
- safety：`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 5. 范围边界

### In Scope

- 新增 Hardware PC gate、artifact/summary、focused tests 和 `pc-tools` / interface docs。
- 新增 Robot diagnostics safe alias、focused tests 和 remote/cloud product docs。
- 新增 `mobile/web` read-only panel、fixture、focused tests 和 mobile user flow docs。
- Product closeout 后续更新 sprint closeout docs、`OKR.md` 和 progress log。

### Out of Scope

- 不做 full Docker build。
- 不改真实硬件配置、UART 参数、launch 串口参数、WAVE ROVER command mode。
- 不接入真实 GitHub thread mutation，不自动 resolve PR #5。
- 不新增 robot control path、ACK/cursor mutation、replay/resubmit、material upload 或 delivery action。
- 不宣称 HIL、true phone/browser proof、O5 external proof、route/elevator field pass、verified terminal result 或 delivery success。

## 6. 优先级和验收口径

P0：

- 所有 surfaces 必须包含 `software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate`。
- 所有 surfaces 必须包含 `source=software_proof`、`hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 所有 docs 必须写明 not HIL、not true phone/browser、not PR #5 resolved、not delivery success。

P1：

- Hardware / Robot / Full-Stack 三路验证命令必须使用 fenced small checks：`py_compile`、focused unittest、`node --check`、`json.tool`、required `rg`、scoped `git diff --check`。
- 代码新增技术注释必须使用中文，并保持注释比例超过 20%；若无法自动统计，worker 必须在 `tech-done.md` 说明检查方式和剩余风险。

P2：

- 文档同步覆盖 `docs/product/`、`docs/interfaces/` 或 `pc-tools/README.md` 中相关 contract，避免代码先行、文档滞后。

## 7. 对应责任 Engineer

- `robot-hardware-engineer`：主责 PC gate 和硬件材料 evidence contract；涉及 vendor/source attribution 时必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向文件。
- `robot-software-engineer`：主责 Robot diagnostics safe alias、remote relay/status surface 和 ROS/API 文档边界。
- `full-stack-software-engineer`：主责 `mobile/web` 只读 panel、fixture、focused tests 和手机流程文档。
- `product-okr-owner`：只负责验收、closeout、OKR snapshot 和 progress log，不写产品代码。

## 8. 风险、阻塞和需要补齐的证据链

- 真实材料仍缺：2D LiDAR SKU/source/receipt、ToF SKU/source/channel-count、mounting/wiring/power plan、calibration material、real HIL-entry、WAVE ROVER powered bench/UART/HIL logs。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；Q/U resolved 不等于 X resolved。
- PR #7 open/no review threads 不能解除 PR #5 material thread。
- Objective 5 仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof 和 verified terminal result。
- 本轮 proof boundary 固定为 `software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate`，不允许在 closeout 中扩大解释。

## 9. 需要创建或更新的 sprint 文档

- 本 planning sprint 已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实施阶段更新：`tech-done.md`。
- 验收阶段更新：`side2side_check.md`。
- 收口阶段更新：`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
