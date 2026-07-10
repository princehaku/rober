# O6/O7 Localization Path Material Readback Tech Done

## sprint_type: epic

本轮 epic 已完成 Algorithm -> O6 -> O7 的 `localization_path_material_readback` 软件证据链。核心结果不是新增一个表面只读区块，而是把 O1 `localization_path_material_bridge` 产出的 same-run localization/path readback 真正接入 O6 archive/readback 和 O7 consumer/UI，并修复三段之间已经暴露的真实 payload shape drift。

## 用户价值和产品北极星

产品北极星仍是：机器人可以被普通用户触发，并可验证地完成垃圾送达。本轮用户价值是让研发、运营和 Product 在同一 `task_id` 详情里看到当前 same-run localization/path 材料的真实状态：map/localization 信号已经出现，但 same-run path generation 仍然失败，因此这不是 route execution success，也不是 delivery success。

本轮不是 production cloud、真实 Nav2 route execution、HIL 或 delivery success 收口；它只把最新 O1 localization/path 材料推进成可复验、可归档、可回读、可展示的软件消费链。

## 实际改动

Algorithm owner `robot-algorithm-engineer` 完成：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/algorithm_worker_report.md`

O6 owner `robot-software-engineer` 完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/o6_worker_report.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/o6_repair_worker_report.md`

O7 owner `full-stack-software-engineer` 完成：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/o7_worker_report.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/o7_repair_worker_report.md`

Product closeout 本轮新增/更新：

- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/tech-done.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/side2side_check.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/final.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/product_worker_report.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 接口和证据链

- Algorithm 新增 `trashbot.localization_path_material_readback.v1` 和 CLI `--localization-path-material-json`。
- O6 新增 `trashbot.o6.localization_path_material_readback.v1` archive/readback/include，覆盖 field evidence、artifact bundle、archive detail、consumer detail 和 `include=localization_path_material_readback`。
- O7 新增 `trashbot.pc_tools_workstation.o7_localization_path_material_readback.v1` default include 和只读 UI summary。
- 全链路 proof boundary 固定为 `software_proof_localization_path_material_readback_only`。
- 全链路继续固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`nav2_route_execution_success=false`、`hil_pass=false`。
- same-run path false 结论继续固定为 `same_run_path_generation_succeeded=false`、`same_run_path_generated=false`、`same_run_path_point_count=0`、`same_run_path_proven=false`；June 11 clean-baseline 只允许出现在 `cross_run_clean_baseline_*` comparator。

## 集成硬化结论

本轮算真实集成硬化，不是 checklist/docs 补丁。原因是三段初版输出并不能直接互通：

- Algorithm 实际输出 `same_run_localization_tf_map_to_odom` / `same_run_localization_tf_map_to_base_link`，并使用 ready status `localization_path_material_readback_ready_not_route_execution_proof`。
- O6/O7 初版更偏向旧字段 `same_run_tf_map_to_odom_observed` / `same_run_tf_map_to_base_link_observed`，且对 status / bridge alias 的预期也不同。
- Repair worker 最终把 O6 和 O7 对齐到“同时接受新旧 alias/status，并继续向 O7 输出 O7-facing aliases”的合同，才让 Algorithm 当前真实 payload 能稳定通过 archive/readback 和 UI 消费链。

## 验证结果

Algorithm owner 验证：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
# 通过，无输出

python3 -m unittest onboard.tests.test_field_route_evidence_manifest
Ran 75 tests in 0.570s
OK

git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback
# 通过，无输出
```

O6 owner 验证：

```text
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 181 tests in 77.953s
OK

python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 181 tests in 77.619s
OK
```

O7 owner 验证：

```text
cd pc-tools/workstation && npm run test && npm run build && npm run lint
Test Files  3 passed (3)
Tests  489 passed (489)
vite v7.3.3 building client environment for production...
eslint .
```

主节点集成验收：

```text
rg anchors 覆盖 O6/O7 alias/status 兼容与 sprint closeout 文档
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback
# 通过，无输出
```

## OKR 映射和方向判断

- O5：继续，主进度维持约 `85%`。本轮没有真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic、真实手机/browser 或 production worker/cutover 材料。
- O1：继续，主进度维持约 `90%`。本轮没有 current same-run HIL、motion command、operator/external observation、current path generation success 或 route execution proof。
- O6：继续，保守从约 `91%` 上调到约 `92%`。理由是 O6 archive/readback 新增 `localization_path_material_readback` additive section，并通过 O6 repair 对齐了 Algorithm 当前真实 payload shape，不再让真实材料在 O6 处误降级。
- O7：继续，保守从约 `91%` 上调到约 `92%`。理由是 O7 consumer/UI 新增 localization/path material summary，并通过 O7 repair 对齐了 O6 初版/返工版 status、TF alias 和 bridge alias，`Tests 489 passed (489)`、build、lint 全通过。

方向判断：继续 O6/O7，但下一轮如果没有更强 live route execution、delivery record、真实/准现场 operator acceptance 或 production cloud readback，不能再靠同层 localization/readback/surface 提升主 OKR。

## KR 拆解和历史归档

本轮不归档 KR。O6/O7 只是新增 localization/path additive 消费链并修复真实 payload drift，尚未满足真实 production cloud、真实 live route execution、真实 delivery record、真实 operator acceptance、真实 delivery success 或长期现场数据回灌的归档阈值。

已完成 KR 历史记录位置保持 `OKR.md` 现有历史区与 `docs/process/okr_progress_log.md`；本轮新增进度只写入当前推进区和进度日志，不移动 KR 到历史区。

## 失败定位

- Algorithm 指定验证最终无失败。
- O6 首轮实现的 comparator 结构在二次 readback 时被误折叠，已由 worker 修复。
- 主节点集成验收发现 O6/O7 初版对 Algorithm 当前 payload 的 status / TF / bridge alias 兼容不足；O6/O7 repair 已修复并复验通过。
- O6 repair 复跑中出现 1 次既有 HTTP connection reset 波动，复跑后 `Ran 181 tests in 77.619s OK`，未见稳定复现。

## 剩余风险

Proof boundary 是 `software_proof_localization_path_material_readback_only`。本轮不证明 production cloud、production DB/queue、TLS/4G、live Nav2 route execution、robot motion、delivery success、operator acceptance、HIL 或 hardware safety。

下一轮有效增长需要补齐更强证据链：同一 `task_id` 的 live route execution、delivery record、真实/准现场 operator acceptance、production cloud/DB/queue readback，或 O1 的当前 same-run HIL/path generation success run。
