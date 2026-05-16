# Sprint 2026.05.16_19-20 Route Task Terminal Review Decision - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：现场支持不应该只拿到“终态复账 software proof 已生成”的技术结论，还要能知道这次为什么仍是 `not_proven`、下一次 field retest 要补哪些真实材料、由哪个 owner 补、哪些动作仍不能在手机端启用。

产品北极星：`rober` 要成为普通手机用户可用、现场可诊断、证据可复盘的低成本 ROS2 自主垃圾投递机器人。本轮把 route/task terminal completion rehearsal 的结果推进为 operator review decision，让下一次真实 Nav2/fixed-route / elevator field session 有明确材料清单，而不是让 Docker-only proof 停在内部摘要。

## 2. OKR 映射

- Objective 5：约 66%，当前数值最低，但本轮不推进。理由是缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；Docker 本地 metadata 不能提升 Objective 5。
- Objective 1：约 75%，下一低，但最近两轮已连续消费 PR #5 硬件基线 / source / precheck blocker；没有真实硬件时，不应第三轮继续堆同类 software gate。
- Objective 2：约 79%，本轮主目标。`route_task_terminal_review_decision` 要把送垃圾任务终态复账转成 review decision、owner handoff、next-required-evidence 和 field retest request guidance。
- Objective 3：约 79%，本轮主目标。review decision 必须点名缺真实 Nav2/fixed-route runtime log、route completion signal、task record 和同一 `evidence_ref` 的现场材料。
- Objective 4：约 88%，本轮间接受益。mobile/web 后续只读 panel 可以让普通用户和现场支持理解 review decision，但不得启用 Start / Confirm Dropoff / Cancel 之外的新控制路径。

## 3. KR 拆解

### KR-A：Operator review decision

把 `route_task_terminal_completion_rehearsal` artifact / summary 转换为 `route_task_terminal_review_decision` artifact / summary，至少输出：

- `review_decision`
- `decision_reason`
- `owner_handoff`
- `next_required_evidence`
- `field_retest_request_guidance`
- safe `evidence_ref`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

### KR-B：Owner handoff

review decision 必须能把缺口映射到 owner：

- Robot Platform Engineer：task record、action result、diagnostics metadata-only consumer。
- Autonomy Algorithm Engineer：Nav2/fixed-route runtime log、route completion signal、fixed-route evidence reconciliation。
- User Touchpoint Full-Stack Engineer：mobile/web 只读展示、copy/export whitelist-only、field retest request guidance。
- Hardware Infra Engineer：只有触及 WAVE ROVER、UART、传感器、电气、HIL 时才介入，并必须先读 `docs/vendor/VENDOR_INDEX.md`。

### KR-C：Field retest request guidance

下一次现场复测材料必须围绕同一 `evidence_ref`，至少要求：

- 真实 Nav2/fixed-route runtime log。
- 真实 task record。
- 真实 route completion signal。
- 真实门状态。
- 真实楼层确认。
- 真实人工协助记录。
- 真实 dropoff/cancel completion 或 delivery result。

### KR-D：Phone-safe read-only surface

mobile/web 后续只能展示 review decision 的安全摘要，不展示 raw JSON、ROS topic、串口、凭证、完整本机路径、checksum、完整 artifact、HIL pass 或成功送达文案。Start / Confirm Dropoff / Cancel gating 不得改变。

## 4. 本轮核心抓手

核心抓手是新增 `route_task_terminal_review_decision` 能力。它不是执行送达，也不是证明送达，而是把上一轮终态复账摘要变成下一次 field retest 的决策包。

证据边界必须统一：

- Evidence boundary：`software_proof_docker_route_task_terminal_review_decision_gate`
- 缺失默认状态：`blocked_missing_route_task_terminal_review_decision`
- 固定声明：`software_proof` only
- 固定结果：`not_proven`
- 固定安全边界：`delivery_success=false`
- 固定控制边界：`primary_actions_enabled=false`

## 5. 需要做什么

P0：

1. Autonomy 新增 dependency-free PC gate，读取 `route_task_terminal_completion_rehearsal` summary，输出 review decision artifact / summary。
2. Robot diagnostics metadata-only 消费该 review decision，缺失、unsupported schema、unsafe fields、same `evidence_ref` mismatch 都 fail closed。
3. mobile/web 新增只读 review decision panel，展示 decision、owner handoff、next-required-evidence 和 field retest request guidance。
4. 文档同步更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。

P1：

1. Product closeout 汇总 worker 验证、更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
2. Final 必须回顾为什么 O5 / O1 本轮不继续推进，并确认本轮只支持 O2 / O3 software proof。

## 6. 优先级和验收口径

P0 验收：

- 能从上一轮 `route_task_terminal_completion_rehearsal` 摘要得到 review decision。
- 输出包含 owner handoff、next-required-evidence、field retest request guidance。
- 缺真实现场材料时状态保持 `not_proven`。
- `delivery_success=false` 和 `primary_actions_enabled=false` 在 PC / Robot / mobile 三端一致。
- mobile/web 不改变 Start / Confirm Dropoff / Cancel gating。

P1 验收：

- docs 同步说明 review decision 是 software proof only。
- `OKR.md` 只按保守 evidence 更新；没有真实外部云或真实硬件材料时，不提升 Objective 5 / Objective 1。
- sprint closeout 不把 review decision 写成真实 field pass、HIL、dropoff completion、cancel completion 或 delivery success。

## 7. 风险、阻塞和证据链

- 最大风险：把 review decision 误读为 delivery success。所有输出必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- O5 阻塞：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- O1 阻塞：缺真实 WAVE ROVER/UART/HIL 和真实传感器材料，且 PR #5 硬件 blocker 已连续消费两轮。
- O2 / O3 待补证据：真实 Nav2/fixed-route runtime log、task record、route completion signal、门状态、楼层确认、人工协助记录、dropoff/cancel completion 或 delivery result。

## 8. 对应责任 Engineer

- Autonomy Algorithm Engineer：PC gate 和 fixed-route workflow docs。
- Robot Platform Engineer：diagnostics metadata-only consumer 和 ROS contract docs。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 panel 和 mobile product flow docs。
- Product Manager / OKR Owner：OKR 映射、sprint closeout、风险边界和验收口径。
