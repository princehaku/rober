# Sprint 2026.05.19_02-03 Elevator Feedback Task Record Trace - PRD

## 用户价值和产品北极星

普通用户在手机端已经能实时看到 `current_step=elevator:<phase>`，但 field owner 结束后仍缺一条可复盘 trace：手机看到的阶段、task_record 落盘内容、diagnostics 摘要和同一 `evidence_ref` 无法一眼对齐。本轮产品价值是把“实时看见电梯阶段”推进成“事后能按同一 evidence_ref 复盘电梯阶段”，降低现场复跑、售后诊断和 PR #4 field material 回填的沟通成本。

产品北极星仍是普通手机用户可解释、可恢复、可复盘地完成低成本 trash delivery。本轮不追求真实 field pass，而是给真实 field pass 准备 post-run trace 契约。

## OKR 映射

- Objective 2：主要推进。KR6/KR7 要求电梯 assisted delivery 进入主链并在 task record/diagnostics 中落盘门状态、楼层证据、人工接管原因和可回放 `evidence_ref`。本轮补的是 `current_step=elevator:<phase>` 到 post-run task_record trace 的桥。
- Objective 4：次要推进。手机端需要让用户和 field owner 看懂上一轮电梯阶段复盘，但必须保持只读、中文优先、phone-safe，不暴露 raw JSON、ROS topic、串口、底层硬件参数或本机路径。
- Objective 5：不推进。O5 约 68% 数字最低，但仍缺真实 HTTPS/TLS、4G/SIM、OSS/CDN、DB/queue、worker/cutover 和 real phone/browser external proof；本轮不得产出 O5 本地 wrapper。
- Objective 1：不推进。O1 约 81%，仍缺真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 真实材料；本轮不得把 trace software proof 写成硬件材料补齐。

## KR 拆解或更新

1. Objective 2 KR7：新增 task_record elevator trace 口径。每次 software-proof 任务结束后，task_record 至少能表达 safe `evidence_ref`、电梯阶段序列、阶段来源、终态、缺失真实材料、`delivery_success=false` 和人工接管/失败原因。
2. Objective 2 KR5：新增 post-run 可复盘记录口径。trace 应能被 diagnostics 和 mobile/web 读取为安全摘要，方便 field owner 对照手机实时阶段与任务结束记录。
3. Objective 4 KR6/KR7：新增手机端“上一轮电梯阶段复盘”只读展示口径。展示只说明阶段和缺口，不启用或暗示 Start Delivery、Confirm Dropoff、Cancel、dropoff completion 或 delivery success。
4. Objective 1 / PR #5：保留独立缺口。2D LiDAR / ToF SKU/vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 不由本轮 trace 关闭。

## 本轮核心抓手

核心抓手是同一 `evidence_ref` 的 post-run trace 对齐：

- 输入：Robot action feedback 已存在 `current_step=elevator:<phase>`，mobile/web 已能实时展示。
- 中间层：Robot 在 task_record 或同等 post-run artifact 中记录 elevator phase timeline。
- 安全摘要：operator diagnostics 暴露 whitelist-only summary，保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 用户触点：mobile/web 展示上一轮电梯阶段复盘，强调“待现场材料回填”，而不是“已完成送达”。

## 需要做什么

### Robot Platform Engineer

- 定义或扩展 task_record post-run trace 字段，表达 `elevator_phase_trace` 或等价结构。
- 将 `current_step=elevator:<phase>` 的阶段序列写入 post-run record 或软件证明 artifact。
- 在 diagnostics 中只读暴露安全摘要，字段需包含 safe `evidence_ref`、trace status、阶段列表、缺失材料、下一步证据和边界 flags。
- 验证未知/缺失/非 elevator phase fail closed，不得输出成功、控制、HIL、field pass 或真实 delivery 结论。

### Full-Stack Engineer

- 在 `mobile/web` 中新增上一轮电梯阶段 trace 只读展示，优先消费 diagnostics/status 中的 safe summary。
- 文案中文优先，不暴露 raw diagnostics、raw JSON、ROS topic、串口、WAVE ROVER 参数、凭证、本机路径或 traceback。
- 保持 primary actions gate 不变：Start Delivery、Confirm Dropoff、Cancel 不因 trace summary 变为 enabled。
- 增加 fixture 和 targeted front-end validation，覆盖 safe summary、缺失 summary、unknown phase 和 boundary flags。

### Hardware Engineer

- 只读核对 PR #5 缺口在本轮文档和 UI copy 中继续独立标注。
- 不修改硬件配置，不新增 UART/baudrate/pin/voltage/firmware/机械尺寸假设。

### Product Owner

- 负责确认本轮仍是 Objective 2 / Objective 4 的 software-proof 规划，不推进 O5 wrapper 或 O1 hardware blocker。
- 实现完成后检查 `docs/` 同步、sprint 留档和 OKR 边界。

## 优先级和验收口径

P0：

- 同一 `evidence_ref` 能在 task_record trace、diagnostics summary 和 mobile trace 中对齐。
- trace 明确 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 未知/缺失/非 `elevator:` 阶段 fail closed。

P1：

- mobile/web 展示用户可读的 post-run 电梯阶段复盘，不与实时阶段 panel 混淆。
- diagnostics summary 只暴露 whitelist-safe 字段，不暴露完整 artifact 或本机路径。
- docs/product 或 docs/interfaces 同步说明 trace contract 和边界。

不验收：

- 真实电梯、真实门状态、真实楼层确认、真实人工协助记录。
- 真实 Nav2/fixed-route runtime、真实 task completion、dropoff/cancel completion、delivery result 或 delivery success。
- O5 external proof、真实手机/browser external proof、WAVE ROVER/UART/HIL、PR #5 2D LiDAR / ToF 材料补齐。

## 风险、阻塞和需要补齐的证据链

- 风险：trace 被误读成真实 field pass。缓解：所有 summary 和 mobile copy 必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 风险：post-run trace 与实时 `current_step=elevator:<phase>` 不一致。缓解：用同一 safe `evidence_ref` 和固定 phase whitelist 做对齐校验。
- 风险：UI 混淆实时状态和历史复盘。缓解：mobile/web 文案明确“上一轮电梯阶段复盘”，并保持只读。
- 阻塞：真实现场材料仍缺。后续 field owner 仍需补真实电梯门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、真实 task_record/completion signal、dropoff/cancel completion 和 delivery result。
- 阻塞：PR #5 硬件材料仍缺。2D LiDAR / ToF 的 SKU/vendor/source、receipt/procurement、installation/wiring/power/calibration、HIL-entry 和 field evidence 必须独立推进。

## 需要创建或更新的 sprint 文档

本规划阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。实现完成前不得预生成 `tech-done.md`、`side2side_check.md`、`final.md`。
