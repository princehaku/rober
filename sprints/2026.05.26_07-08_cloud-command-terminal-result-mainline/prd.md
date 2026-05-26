# Cloud Command Terminal Result Mainline PRD

## 1. 背景

`cloud_phone_command_api` 已能让手机发起 collect、confirm-dropoff、cancel 命令；`cloud_command_result_reconciliation` 已能让手机查询 queued、processing、terminal_result_pending、missing_or_expired 和 store_unavailable。

当前缺口是：terminal ACK 只是 cloud command envelope 终态，不能说明机器人任务真正产出了 delivery/dropoff/cancel terminal result。用户和支持人员仍然无法按同一 `robot_id + command_id` 查到 robot/relay 写入并持久化的终态结果。

本轮 PRD 要求把 O5 从“可解释 pending”推进到“cloud_command_terminal_result 主路径”：有写入口、有持久化、有查询状态、有 mobile/web 展示，同时保持 fail-closed。

## 2. 用户价值和产品北极星

北极星：普通手机用户不懂 ROS2、队列、ACK 或 WAVE ROVER，也能知道自己发出的垃圾投递命令当前处于什么终态、是否仍需要等待真实现场材料，而不是被技术性 ACK 误导。

用户价值：

- 用户看到命令终态结果：例如处理完成、投放确认完成、取消完成、失败、超时或被拒绝。
- 支持人员能拿同一 `robot_id + command_id` 对账 command receipt、ACK、terminal result 和 evidence boundary。
- 产品口径清楚区分 software terminal result 与真实 delivery success，避免把本地 Docker proof 包装成真实送达。

## 3. OKR 映射

- Objective 5：直接推进云中转命令结果主链路，预期可从约 76% 小幅提升，具体提升在 `final.md` 根据实现证据决定。
- Objective 1：不涉及 WAVE ROVER/UART/HIL，保持约 83%。
- Objective 2：不证明真实送垃圾任务完成、dropoff/cancel field completion 或 delivery success，保持约 99%。
- Objective 3：不证明 Nav2/fixed-route runtime 或 route/elevator field pass，保持约 99%。
- Objective 4：mobile/web 会展示新状态，但不是真实 iPhone/Android/browser proof，保持约 99%。

## 4. 产品范围

### In Scope

- Robot/cloud relay 接收 terminal result 的 robot-facing API。
- Store 按同一 `robot_id + command_id` 持久化 terminal result。
- Result reconciliation API 返回新的 terminal result recorded 状态。
- mobile/web 展示 terminal result 终态和下一步证据要求。
- `docs/product/` 在实现阶段同步更新。
- backend 和 mobile/web tests 覆盖成功、失败、缺失、冲突和 store unavailable。

### Out of Scope

- 真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、worker cutover。
- OSS/CDN live upload 或 CDN 回源实证。
- WAVE ROVER、UART、HIL、2D LiDAR、ToF 或 PR #5 resolution。
- Nav2/fixed-route runtime、真实电梯、真实路线、真实投放。
- 把任何状态写成 `delivery_success=true`。
- 新增 metadata-only `*_review_*`、`*_handoff_*`、`*_material_*` wrapper 作为主交付。

## 5. 核心用户故事

1. 作为手机用户，我发出 collect 命令后，能刷新命令结果并看到“机器人已上报终态结果”，而不是永远停在 terminal result pending。
2. 作为支持人员，我能用 `robot_id + command_id` 查到 terminal result 的类型、状态、错误码、时间和下一步证据缺口。
3. 作为产品负责人，我能确认 UI 没有把 terminal ACK 或 software proof terminal result 误写成真实送达成功。

## 6. Terminal Result 产品语义

能力名：`cloud_command_terminal_result`

建议 schema：

- 写入 schema：`trashbot.cloud_command_terminal_result.v1`
- 查询 schema：`trashbot.cloud_command_result_reconciliation.v2`
- evidence boundary：`software_proof_docker_cloud_command_terminal_result_gate`

建议 terminal result 状态：

- `terminal_result_recorded`：同一 `robot_id + command_id` 下已有 phone-safe terminal result。
- `terminal_result_pending`：ACK 已终态，但 terminal result 仍缺失。
- `terminal_result_conflict`：重复写入与已持久化结果不一致。
- `terminal_result_missing`：command 不存在、过期或没有 result。
- `store_unavailable`：store 读写失败。

建议 terminal result 类型：

- `delivery_terminal`
- `dropoff_terminal`
- `cancel_terminal`
- `failure_terminal`
- `timeout_terminal`
- `rejected_terminal`

所有状态必须同时保留：

- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `real_world_delivery_proven=false`
- `next_required_evidence`
- 普通中文 `safe_copy`

## 7. 验收口径

### P0 验收

- Robot/relay 有 robot-facing terminal result 写入入口，不通过 phone route 伪造。
- Terminal result 写入必须校验 command 存在、robot_id 匹配、command_id 匹配。
- Store 能持久化 terminal result，并被 result reconciliation API 读取。
- Result reconciliation 对有 terminal result 的 command 返回 `terminal_result_recorded` 或等价新状态。
- mobile/web 能显示 terminal result recorded 状态、result type、result code/error code、safe copy 和 next required evidence。
- 所有路径继续 fail-closed：`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。

### P1 验收

- 重复写入同一 terminal result 幂等。
- 冲突写入返回 phone-safe conflict，不覆盖既有 result。
- 缺失 command、robot_id 不匹配、store unavailable 都返回脱敏错误。
- UI 不自动 replay、不 resubmit、不请求 ACK cursor、不暴露 raw diagnostics。

### 反验收

以下任一情况发生则本 sprint 不可收口为 O5 进展：

- 只新增 review/handoff/material/intake metadata wrapper。
- 只更新 mobile/web fixture，不改 backend 写入和 store。
- Terminal result 只存在响应内，不持久化。
- 查询 API 仍只能返回 `terminal_result_pending`。
- UI 或文档出现 `delivery_success=true`、真实送达已完成、HIL 已通过、真实 4G 已通过等误导文案。

## 8. 优先级

- P0：Robot API/store/query 主链路。
- P0：mobile/web terminal result recorded 展示和 fail-closed copy。
- P0：backend/mobile tests 覆盖主状态和失败状态。
- P1：docs/product 同步。
- P1：closeout 更新 `OKR.md`、`tech-done.md`、`side2side_check.md`、`final.md`。

## 9. 对应责任 Engineer

- Robot Software Engineer：API、store、result reconciliation、backend tests、cloud docs。
- User Touchpoint Full-Stack Engineer：mobile/web UI、fixture、tests、mobile docs。

## 10. 风险、阻塞和证据链

- 真实 terminal result 不等于真实世界送达；必须保留 software proof 边界。
- 如果 backend store 当前没有 terminal result 数据模型，Robot Software Engineer 需要先补最小结构再接 API。
- 如果 mobile/web 已有大量 terminal result material panels，本轮必须复用或压缩展示，不再新增一串 review/handoff wrapper。
- 缺真实公网、4G、生产 DB/queue、OSS/CDN、HIL、Nav2/fixed-route、真实手机设备和现场送达材料；这些必须在 closeout 中继续列为剩余风险。
