# PRD - O7 Mission Evidence Bundle Export

## 用户问题

O7 已能按 selected task 做 query、event append、inference request 和 delivery result intake，但 reviewer 仍需要在多个 section 之间手动拼接证据。对运营调试和训练数据准备来说，当前 selected task 缺少一个保守的 bundle export 摘要，无法快速说明“这次任务已经有哪些可审计材料、还缺什么、为什么不能算送达成功”。

## 产品目标

提供 O7 selected-task mission evidence bundle export，使 operator/reviewer 能从 PC 工作站拿到一个单任务、同一 `task_id`、fail-closed 的 evidence bundle receipt。

这个 receipt 必须：

- 聚合同一 task 的 O6 consumer detail 可读材料。
- 总结 mission events、field evidence、same-task replay packet、delivery result/readiness、route execution readiness 或 closure packet 等关键证据状态。
- 明确 proof boundary 为 local/mock software proof only。
- 固定 `safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`robot_control_executed=false`、`connects_cloud_production=false`。
- 给出缺口：production cloud、route execution、delivery/operator acceptance、HIL、safe-to-control、real dataset export。

## 非目标

- 不连接公网生产云。
- 不上传 OSS/CDN。
- 不执行机器人控制。
- 不读取或写入 WAVE ROVER UART。
- 不下发 `/cmd_vel`、`/api/base/manual` 或 NavigateToPose。
- 不把 local/mock bundle 当真实训练集导出。

## 主要用户流

1. Operator 在 O7 consumer read primary path 选中 task。
2. Operator 点击 mission evidence bundle export。
3. PC 后端 adapter 只访问本机回环 O6 consumer detail endpoint。
4. Adapter 校验 schema、task identity、dangerous true fields 和 unsafe content。
5. Adapter 返回 O7 bundle export receipt，UI 展示 bundle status、source section counts、material refs basename、blocked reasons 和 fixed false fields。

## 验收标准

- 新 O7 endpoint 存在，路径建议为 `GET /api/o7/consumer-read/tasks/<task_id>/mission-evidence/export?baseUrl=<local-loopback-url>&format=json`。
- 非回环 URL、credential/query/hash、task mismatch、schema mismatch、dangerous true fields、unsafe refs 均 fail closed。
- 成功响应包含 stable schema，例如 `trashbot.pc_tools_workstation.o7_mission_evidence_bundle_export_result.v1`。
- 成功响应包含 `bundle_status=local_mock_mission_evidence_bundle_ready`。
- 响应包含 source section summary 和 fixed false safety fields。
- Workstation tests/build/lint 通过；如 build 只保留既有 Vite large chunk warning，需要在 `tech-done.md` 记录。

## OKR 口径

本轮只作为 O7/O6 local/mock evidence packaging/export increment。它比 query/readback wrapper 更强，因为它直接围绕 selected task 汇总 mission evidence bundle；但仍不提升 O5，不归档 KR，不证明真实 route execution、delivery、HIL、safe-to-control 或 production cloud。
