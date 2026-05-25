# Cloud Command Result Reconciliation Side2Side Check

## 1. 用户价值核对

本轮面向的用户问题是：手机端发出“开始送垃圾 / 确认投放 / 取消”后，不能只看到 queued receipt，还要能查询命令现在处于队列、处理中、终态 ACK 但结果缺失，还是暂时无法确认。

核对结论：本轮已经从单纯入队 API 前进到命令 lifecycle/result reconciliation。用户能获得更可信的等待/处理中/待核验证据解释，但仍不能把任何状态理解成真实送达成功。

## 2. Side-by-side 验收

| 用户看到的状态 | 产品解释 | 是否可写成成功 |
| --- | --- | --- |
| queued | 云端已接收并入队，等待机器人领取或处理 | 否 |
| processing | 命令已被接收/处理中，尚无真实 delivery/dropoff/cancel result | 否 |
| terminal_result_pending | 命令已有 terminal ACK，但 verified terminal result 仍缺失 | 否 |
| missing_or_expired / unavailable | 暂时无法确认命令状态，请等待或联系支持 | 否 |

## 3. OKR 映射

- Objective 5：直接推进 commands/status/ack 最小契约，从 phone -> cloud command enqueue 补齐到 command result reconciliation。
- KR1：新增 `trashbot.cloud_command_result_reconciliation.v1` 和 `cloud_command_result_reconciliation`，补齐 phone-safe 查询入口。
- KR6：补齐 store unavailable / missing_or_expired 的 fail-closed 状态解释。
- Objective 4：只获得手机 copy 和只读面板体验收益；由于没有 true phone/browser proof，不提升 Objective 4。

## 4. 证据链核对

- Robot worker 证据：`GET /api/commands/{command_id}/result?robot_id=<robot_id>`，schema `trashbot.cloud_command_result_reconciliation.v1`，boundary `software_proof_docker_cloud_command_result_reconciliation_gate`，目标测试 `Ran 7 tests ... OK`。
- Full-Stack worker 证据：mobile/web 只读结果核对面板、fixture 和文档，四类中文 copy，目标测试 `Ran 4 tests ... OK`。
- 两边 `git diff --check` 通过。

## 5. 不能宣称的范围

本轮不证明公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、true phone/browser proof、HIL、Nav2/fixed-route、WAVE ROVER/UART 或 delivery success。它也不证明真实 dropoff/cancel completion、verified terminal delivery/dropoff/cancel result、route/elevator field pass、PR #5 resolved 或真实 production queue recovery。

## 6. Product 验收结论

本轮满足 Epic closeout 条件：能力、copy、false-state、worker 验证与 sprint 留档闭环成立。Objective 5 可从约 72% 小幅提升到约 76%；Objective 1/2/3/4 保持不变。
