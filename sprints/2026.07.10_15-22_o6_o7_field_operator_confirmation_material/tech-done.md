# O6/O7 Field Operator Confirmation Material Tech Done

## sprint_type: epic

本轮 epic 已完成 Algorithm -> O6 -> O7 的 `field_operator_confirmation_material` 软件证据链。核心结果是把同一 `task_id` 下的 operator report / operator confirmation material 归一为安全、只读、可归档、可回读、可展示的 additive material，而不是把 operator material 解释为 delivery success。

## 用户价值和产品北极星

产品北极星仍是：机器人可以被普通用户触发，并可验证地完成垃圾送达。本轮用户价值是让研发、运营和 Product 能在同一任务详情里看到 operator report / operator confirmation material 是否已被接入、哪些材料已 present、哪些证据仍不足以证明真实路线执行或送达完成。

本轮不是生产云、真实 Nav2 route execution、HIL 或 delivery success 收口；它只把 operator 材料从零散报告推进到可复验的软件消费链。

## 实际改动

Algorithm owner `robot-algorithm-engineer` 完成：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/algorithm_worker_report.md`

O6 owner `robot-software-engineer` 完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/o6_worker_report.md`

O7 owner `full-stack-software-engineer` 完成：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/o7_worker_report.md`

Product closeout 本轮新增/更新：

- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/tech-done.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/side2side_check.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/final.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/product_worker_report.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 接口和证据链

- Algorithm 新增 `trashbot.field_operator_confirmation_material.v1` 和 CLI `--field-operator-confirmation-json`。
- O6 新增 `trashbot.o6.field_operator_confirmation_material.v1` archive/readback/include，覆盖 field evidence、artifact bundle、archive detail、consumer detail 和 `include=field_operator_confirmation_material`。
- O7 新增 `trashbot.pc_tools_workstation.o7_field_operator_confirmation_material.v1` default include 和只读 UI summary。
- 全链路 proof boundary 固定为 `software_proof_field_operator_confirmation_material_only`。
- 全链路继续固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。

## 验证结果

Algorithm owner 验证：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
# 通过，无输出

python3 -m unittest onboard.tests.test_field_route_evidence_manifest
Ran 73 tests in 0.543s
OK

git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material
# 通过，无输出
```

O6 owner 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
# 通过，无输出

python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 177 tests in 75.477s
OK
```

O7 owner 验证：

```text
cd pc-tools/workstation && npm run test && npm run build && npm run lint
Test Files  3 passed (3)
Tests  487 passed (487)
vite v7.3.3 building client environment for production...
34 modules transformed.
built in 1.81s
eslint .
```

主节点集成验收：

```text
rg anchors 覆盖 onboard/docs/pc-tools/sprint
git diff --check
# 全仓无输出
```

Product closeout 验收命令记录在 `artifacts/product_worker_report.md`，最终复验包括 `field_operator_confirmation_material`、`software_proof_field_operator_confirmation_material_only`、`O6`、`O7`、`91`、`Ran 73 tests`、`Ran 177 tests` 和 `487 passed` 锚点。

## OKR 映射和方向判断

- O5：继续，主进度维持约 `85%`。本轮没有真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic、真实手机/browser 或 production worker/cutover 材料。
- O1：继续，主进度维持约 `86%`。本轮没有真实 WAVE ROVER nonzero L/R、轮速方向、motion command、同 run HIL acceptance 或 hardware safety 材料。
- O6：继续，保守从约 `90%` 上调到约 `91%`。理由是 O6 archive/readback 新增了 operator report / operator confirmation material 的可回读 additive section，并通过 177 tests。
- O7：继续，保守从约 `90%` 上调到约 `91%`。理由是 O7 consumer/UI 默认 include 并展示 operator material summary，并通过 487 tests、build、lint。

方向判断：继续 O6/O7，但下一轮如果没有更强 live route execution、delivery record、真实 operator acceptance 或 production cloud readback，不能再靠同层只读 material wrapper 提升主 OKR。

## KR 拆解和历史归档

本轮不归档 KR。O6/O7 只是新增 operator material additive 消费链，尚未满足真实 production cloud、真实 live route execution、真实 delivery record、operator acceptance、delivery success 或长期现场数据回灌的归档阈值。

已完成 KR 历史记录位置保持 `OKR.md` 现有历史区与 `docs/process/okr_progress_log.md`；本轮新增进度只写入当前推进区和进度日志，不移动 KR 到历史区。

## 失败定位

- Algorithm 和 O6 指定验证均一次通过，没有未修复失败。
- O7 初次 `npm run test` 暴露 catalog default include 断言仍缺 `field_operator_confirmation_material`，已修复。
- O7 combined acceptance 中 `npm run build` 暴露 `failClosedDetail` 漏传 field operator material 参数，以及 fixture 中 fixed false 字段重复声明问题，均已修复并复验通过。

## 剩余风险

Proof boundary 是 `software_proof_field_operator_confirmation_material_only`。本轮不证明 production cloud、production DB/queue、TLS/4G、live Nav2 route execution、robot motion、delivery success、operator acceptance、HIL 或 hardware safety。

下一轮有效增长需要补齐更强证据链：同一 `task_id` 的 live route execution、delivery record、真实/准现场 operator acceptance、production cloud/DB/queue readback，或 O1 的真实 WAVE ROVER nonzero/HIL run。
