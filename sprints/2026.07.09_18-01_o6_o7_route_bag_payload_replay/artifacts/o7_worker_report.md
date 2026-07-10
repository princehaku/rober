# O7 Worker Report

- 任务：接入 `route_bag_payload_replay` 到 O7 consumer adapter、shared contracts、fixture preview UI 和相关测试。
- 范围：`pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`、`pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`、`docs/product/pc_tools_workstation.md`。

## 实际改动

- 在 [`pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts) 中让 O7 默认读取 `route_bag_payload_replay`，并把它汇总进 `artifact_bundle`、`artifact_bundle_consumer_ingest`、`artifact_bundle_readiness`、`route_bag_evidence` 和 `consumer detail`。
- 在 [`pc-tools/workstation/src/shared/contracts.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts) 中新增 `O7ConsumerRouteBagPayloadReplaySummary`，并把 `route_bag_payload_replay` 挂进相关 summary/detail contract。
- 在 [`pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`](/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue) 中补齐 route bag payload replay 的只读展示，包含 source/status、topic/message/timestamp、payload size/hash prefix、blocked reasons、next evidence 和 false safety fields。
- 在 [`pc-tools/workstation/test/catalog.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts) 和 [`pc-tools/workstation/test/App.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts) 中补了 payload replay fixture、include 策略和 fail-closed 断言。
- 在 [`docs/product/pc_tools_workstation.md`](/Users/m1/apps/rober/docs/product/pc_tools_workstation.md) 中同步更新 O7 工作站说明，明确 `route_bag_payload_replay` 的只读边界和 fail-closed 规则。

## 验证结果

- `npm run test`：通过，`3` 个测试文件、`479` 个测试全部通过。
- `npm run build`：通过；Vite 产物成功输出，只有 chunk size 500k+ 的既有警告。
- `npm run lint`：通过。
- `rg -n "route_bag_payload_replay|software_proof_route_bag_payload_replay_only|safe_to_control|delivery_success" ...`：命中相关适配器、契约、UI、测试和文档位置。
- `git diff --check -- ...`：通过，未发现空白或格式问题。

## 失败定位

- 过程中曾出现三类问题：
- payload replay 先只从部分直连路径读取，后来补了 `field_evidence_consumer_ingest` / `field_evidence_ingest` 的直连入口。
- dangerous true 早退先返回了泛化原因，后改成直接返回 `route_bag_payload_replay_dangerous_true:*` 专用理由。
- fixture 先缺少顶层 `route_bag_payload_replay`，导致 preview UI 没有稳定展示该证据；后在 artifact bundle / consumer ingest 侧补齐。
- 这些问题已修复并重新验证通过。

## 剩余风险

- `route_bag_payload_replay` 目前仍是只读安全摘要，不证明真实 ROS2 runtime、真实底盘运动、真实 route execution success 或 delivery success。
- 该链路依赖 O6 侧继续维持 `trashbot.route_bag_payload_replay.v1` / `trashbot.o6.route_bag_payload_replay.v1` 和 `software_proof_route_bag_payload_replay_only` 的契约稳定性。
- 如果未来 O6 侧再调整嵌套位置或字段名，需要同步回看 adapter 的下钻路径和 fail-closed 测试。
