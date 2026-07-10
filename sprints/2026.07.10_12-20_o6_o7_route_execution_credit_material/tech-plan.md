# O6/O7 Route Execution Credit Material Tech Plan

## 技术方案

在现有 `same_task_route_execution_material_packet` 上做向后兼容扩展，不新增 raw artifact 入口：

- Algorithm 从现有安全摘要判断：
  - live/field command evidence：`motion_log_summary.live_motion_evidence_present`、`motion_log_summary.live_nav2_log_present` 或 `route_bag_or_live_nav2_log.source=live_motion_log`。
  - delivery/operator material：已消费 `delivery_result_evidence` 且 `delivery_result_claimed=true` 或 `operator_confirmation_present=true`。
  - credit candidate：`route_execution_material_consumed=true` 且 live/field command evidence 与 delivery/operator material 同时成立。
- O6 只保留布尔、短 reason、短 next evidence list；所有危险 true、unsafe text、path/token/raw/base64 继续降级当前 section。
- O7 只展示 credit material status，不派生真实成功或控制权限。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective：O5 约 `85%`；其次 O1 约 `86%`；O6/O7 约 `87%`。
2. 本 sprint 不针对绝对最低 O5。
3. 不继续 O5 的理由：最近 O5 final 已要求真实 production cloud、production DB/queue external probe 或真实 live endpoint evidence；当前环境没有这些外部材料，继续 local/mock probe/readback 会违反 support-only 不加分规则。
4. 不继续 O1 的理由：当前可读旧日志仍为 `T=1001` 但 `L=0,R=0`，缺真实 nonzero feedback、轮向、operator report 与 HIL acceptance；继续 software gate 包装不应计进度。
5. 本 sprint 选择 O6/O7 的理由：上轮 final 指定下一步必须接 live route execution、delivery record 或 operator confirmation。本轮把这些材料是否存在、是否可计 credit 的判断固化到同一 packet，是从 wrapper 进入 mission artifact delta 的必要中间层。

## Owner Split

### Robot Algorithm Engineer

文件范围：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/artifacts/algorithm_worker_report.md`

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material
```

### Robot Software Engineer / O6

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/artifacts/o6_worker_report.md`

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material
```

### Full-Stack Software Engineer / O7

文件范围：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/artifacts/o7_worker_report.md`

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material
```

## 主节点验收

```bash
rg -n "route_execution_credit_candidate|credit_support_only_reason|live_or_field_command_evidence_present|delivery_or_operator_material_consumed|o6_o7_route_execution_credit_material" onboard pc-tools docs sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material OKR.md
git diff --check
```

## 风险

- 如果 worker 只能完成 Algorithm 或 O6/O7 的单侧改动，必须标记 chain incomplete，不调整 OKR。
- 如果新字段只在 fixture 里 ready、没有 live/field command evidence，必须输出 support-only，不允许 `okr_credit_allowed=true`。
- 本轮不证明真实送达成功、真实生产云、真实机器人运动或硬件安全。
