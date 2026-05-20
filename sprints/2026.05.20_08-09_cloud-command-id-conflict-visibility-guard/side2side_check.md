# Sprint 2026.05.20_08-09 Cloud Command ID Conflict Visibility Guard - Side2Side Check

## 1. 验收对象

- sprint_type: epic
- 验收主题：`cloud_command_id_conflict_visibility_guard`
- 目标证据边界：`software_proof_docker_cloud_command_id_conflict_visibility_guard`

## 2. 用户价值核对

| 验收项 | 结果 |
| --- | --- |
| 同一 `command.id` + 同内容重复提交仍可 dedupe | 通过，Robot worker 回传 same-content duplicate still dedupes。 |
| 同一 `command.id` + mismatched `type` fail closed | 通过，Robot 输出 `command_id_conflict` 并拒绝执行。 |
| 同一 `command.id` + mismatched `payload` fail closed | 通过，canonical identity 使用 sorted JSON payload，冲突拒绝执行。 |
| conflict 不复用 cached ACK | 通过，Robot 回传 does not reuse cached ACK。 |
| conflict 不启用主操作 | 通过，`primary_actions_enabled=false` 保持。 |
| 手机端中文解释冲突 | 通过，mobile/web 展示“命令 ID 冲突；机器人已拒绝执行；这不是送达成功。” |
| 手机端不新增控制副作用 | 通过，Full-Stack 回传没有 replay/resubmit/ACK/cursor endpoint。 |

## 3. OKR 映射核对

- Objective 5：本轮推进 command/status/ack 控制面冲突安全可见性，但只记为 `software_proof_docker_cloud_command_id_conflict_visibility_guard`，进度保持约 68%。
- Objective 4：本轮让手机端可读冲突状态并 fail closed，但不是真实手机/browser 验收，进度保持约 99%。
- Objective 1：本轮不涉及 WAVE ROVER/UART/HIL 或 2D LiDAR / ToF 材料，进度保持约 81%。

## 4. 边界核对

本轮明确不证明：

- 真实公网 HTTPS/TLS
- 4G/SIM
- OSS/CDN live traffic
- production DB/queue
- production worker/migration/cutover
- 真实手机/browser
- WAVE ROVER/UART/HIL
- Nav2/fixed-route 实跑
- route/elevator field pass
- dropoff/cancel completion
- delivery success

PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；本 sprint 不关闭该 thread，也不补齐真实 2D LiDAR / ToF 材料。

## 5. 验收结论

本轮达到 PRD 中的 P0/P1 软件验收口径：冲突命令被拒绝、可见、不可误认为 cached ACK 或送达成功，手机主操作继续关闭。由于没有真实 external / hardware / phone 材料，本轮不提升 Objective 5、Objective 4 或 Objective 1 completion。
