# O6/O7 Same-Task Route Execution Material Packet Final

## 用户价值和产品北极星

产品北极星：普通用户把垃圾交给机器人后，机器人能沿固定路线完成可验证、可复盘、可恢复的送达任务。

本轮用户价值是把“同一 `task_id` 是否已经消费 route execution 相关材料”从分散 summary 深化为 Algorithm -> O6 -> O7 都可读的安全 packet。运营人员现在可以看到 route execution material status、材料摘要、blocked reasons 和 next required evidence，而不是只看到 checklist 或 wrapper 已存在。

## OKR 映射和方向判断

| Objective | 判断 | 进度建议 | 理由 |
| --- | --- | --- | --- |
| O6 云端核心后端 | 继续 | `~86%` -> `~87%` | O6 archive/readback 新增 `trashbot.o6.same_task_route_execution_material_packet.v1`，同 task route execution material 可通过 archive detail、field evidence、artifact bundle、consumer detail 和 include 回读 |
| O7 PC 端运营调试平台 | 继续 | `~86%` -> `~87%` | O7 默认 include/UI 独立展示新 packet，能消费 O6 顶层 status、材料摘要、blocked reasons、next evidence 和 fixed false flags |
| O5 云中转控制面 | 暂停本轮进度调整 | 维持 `~85%` | 没有新增真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic 或真实手机/browser 证据 |
| O1 硬件协议可信底盘 | 暂停本轮进度调整 | 维持 `~86%` | 没有新增真实 WAVE ROVER nonzero L/R、轮速方向、真实 robot motion 或 HIL acceptance record |

本轮方向判断：O6/O7 继续，但下一步必须从 packet consumption 进入 live route execution、delivery record、operator confirmation 或 production cloud readback。若这些材料不可得，后续同类工作只能作为回归守护，不应继续提升主 OKR。

## KR 拆解、更新和历史归档

- 本轮不归档任何 KR。
- O6 KR2/KR6 得到局部推进：任务记录/感知事件 archive/readback 与 consumer API 更能表达 route execution material packet。
- O7 KR3 得到局部推进：历史路线回放/任务详情可读的 route execution material 摘要更完整。
- O7 KR4 仅间接受益：材料摘要和 evidence refs 更适合后续标注/训练入口，但本轮不证明真实 annotation API/export。
- 已完成 KR 历史记录位置：无新增归档；历史归档仍在 `docs/process/okr_progress_log.md` 和 `OKR.md` 已归档 Objective 表中。

## 本轮核心抓手

- Algorithm producer：新增 `trashbot.same_task_route_execution_material_packet.v1`，把 field material、route execution readiness/closure、Nav2、delivery result、pose progress、route bag replay 和 replay JSONL 归一为安全摘要。
- O6 contract source：新增 `trashbot.o6.same_task_route_execution_material_packet.v1`，统一 archive/readback/include/consumer detail 回读，并对 unsafe/mismatch/dangerous true fail-closed。
- O7 read-only consumer：默认 include 新 packet，独立展示 O6 顶层状态、材料摘要、blocked reasons、next required evidence 和 fixed false flags。

## 验证证据

| Owner | 验证结果 |
| --- | --- |
| Robot Algorithm Engineer | `python3 -m unittest onboard.tests.test_field_route_evidence_manifest` 输出 `Ran 65 tests in 0.453s` / `OK`；`py_compile` 和 scoped `git diff --check` 通过 |
| Robot Software Engineer / O6 | `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 171 tests in 68.334s` / `OK`；`py_compile` 通过 |
| Full-Stack Software Engineer / O7 | `cd pc-tools/workstation && npm run test && npm run build && npm run lint` 通过，关键输出 `Tests 486 passed (486)`，build 和 lint exit code 0 |

## 需要做什么

1. 下一轮若继续 O6/O7：接同一 `task_id` 的 live route execution result、delivery record 或 operator confirmation，而不是继续增加只读 wrapper。
2. 若 production cloud/DB/queue 材料可得：优先切回 O5，跑真实 production endpoint/DB queue readback。
3. 若硬件材料可得：切回 O1，消费真实上车 `feedback_T1001.log`、motion command、operator report 和 HIL acceptance record。

## 优先级和验收口径

- P0：同一 `task_id` 的 live route execution result 或可复验 replay JSONL，必须进入 Algorithm -> O6 -> O7 链路。
- P0：delivery record / operator confirmation 不能只存在 UI 文案，必须有 task artifact 和 readback。
- P0：所有 safety/control/delivery flags 继续固定 false，除非真实安全准入和现场送达证据齐备。
- P1：production cloud / DB queue / OSS readback 与同 task route execution packet 关联。
- P2：O7 展示更丰富 timeline，但不得替代 P0 现场/生产证据。

## 对应责任 Engineer

- `robot-algorithm-engineer`：继续生产 live route execution / replay / delivery material producer。
- `robot-software-engineer`：继续维护 O6 archive/readback 合同、fail-closed sanitizer 和 production readback。
- `full-stack-software-engineer`：继续维护 O7 read-only consumer/UI、default include 和 operator material visibility。
- `rober-hardware-engineer`：当 O1 真实 run 材料可得时，负责 WAVE ROVER/HIL evidence。

## 风险、阻塞和证据链缺口

- 当前证据边界是 `software_proof_same_task_route_execution_material_packet_only`。
- 不证明真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic。
- 不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 不证明 hardware safety、WAVE ROVER nonzero L/R、wheel direction 或 HIL pass。
- 不证明真实 annotation API/export 或长期路线验收。

## Sprint 文档状态

- 已创建/更新：`tech-done.md`、`side2side_check.md`、`final.md`、`artifacts/product_worker_report.md`。
- 已更新：`OKR.md`、`docs/process/okr_progress_log.md`。
- 未创建 KR 历史归档条目；本轮没有 KR 达到完成/取消/替换条件。
