# Same-Task Mission Artifact Credit Gate Final

## 复盘结论

本轮 epic sprint 完成。用户价值不是再做一层 wrapper，而是把“哪些 same-task mission materials 允许计入主 OKR 进度”变成硬 gate：没有新的 live/field mission artifact delta 时，系统必须显式输出 `okr_credit_allowed=false` 和 `support_only_reason`，并阻止 O5/O6/O7 因 support-only surface 继续加分。

产品北极星仍是可验证地可靠交付垃圾。本轮没有消费新的真实 production cloud、真实 live route execution、真实 delivery record、真实 operator confirmation 或真实 delivery success，因此它是 support-only hard gate / credit gate 软件合同，不是新的 mission 成功证据。

## OKR 映射和进度调整

- O5 / KR1 / KR6：继续，但不调整，维持约 `85%`。本轮只把 same-task mission credit 误判从流程口径变成软件合同，没有新增真实 production cloud、production DB/queue external probe 或真实 live endpoint evidence。
- O6 / KR2 / KR6：继续，但不调整，维持约 `85%`。archive/readback 现在能回读 credit fields 并对 support-only fail-closed，但未新增真实 production cloud、真实隧道、真实机器人数据、真实 delivery record 或真实 delivery success。
- O7 / KR3 / KR4：继续，但不调整，维持约 `85%`。O7 现在能展示 credit gate 并把 `okr_credit_allowed=false` 收紧为 support-only/blocked，但未消费新的真实或准现场 same-task materials。
- O1：继续但不调整，维持约 `85%`。本轮未补轮速非零原始反馈、轮速方向或 HIL 证据。

本轮不归档任何 KR。原因不是工作无效，而是其产出属于“防止错误记分”的合同硬化，不构成新的 mission 主证据增量。

## 实际交付

### Engineer 交付

- Robot Algorithm：在 `field_route_evidence_manifest.py` 新增结构化 `mission_artifact_delta` 与 `same_task_id_consumed`、`live_or_field_command_executed`、`support_only_reason`、`okr_credit_allowed`，并补充 manifest 单测与文档。
- Robot Software / O6：在 `remote_cloud_relay.py` 接住结构化 credit fields，archive detail / field evidence / consumer detail / include 均可回读，并对 support-only、缺字段、legacy unstructured delta、unsafe text、dangerous true、task mismatch fail-closed。
- Full-stack / O7：在 consumer adapter、contracts、fixture preview panel 和测试中展示 credit fields，并把 `okr_credit_allowed=false` 明确渲染成 support-only/blocked，不再把 checklist ready 误视为可计主 OKR 进度。

### Product 交付

- 回填 `tech-done.md`，补齐被并行写覆盖的 Algorithm / O6 汇总段。
- 创建 `side2side_check.md` 与本文件，形成 Epic 完整收口链路。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`，把“support-only 不加主进度”固化为当前产品方向判断。
- 更新 `artifacts/product_worker_report.md`，汇总三位 worker 的验证证据和 Product 判定。

## 验证证据

- Algorithm：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py` 通过；`python3 -m unittest onboard.tests.test_field_route_evidence_manifest` 输出 `Ran 60 tests in 0.313s OK`；`git diff --check` 通过。
- O6：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 通过；`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 168 tests in 64.612s OK`；`git diff --check` 通过。
- O7：`cd pc-tools/workstation && npm run test` 输出 `Tests 484 passed (484)`；`npm run build` 输出 `built in 1.78s` 并保留既有 Vite chunk warning；`npm run lint` 通过；`git diff --check` 通过。
- Product closeout：本 sprint `tech-done.md`、`side2side_check.md`、`final.md` 已创建；`rg -n "okr_credit_allowed|support_only_reason|mission_artifact_delta|same_task_id_consumed"` 命中 sprint、`OKR.md` 与 `docs/process/okr_progress_log.md`；`git diff --check` 通过。

## 证据边界

本轮 proof boundary 可表述为 `software_proof_same_task_mission_artifact_credit_gate_only`。

它证明 same-task mission credit 的判定规则已经在 Algorithm manifest、O6 archive/readback 和 O7 consumer/UI 三层可执行、可回读、可 fail-closed。

它不证明真实 production cloud、production DB/queue、多实例一致性、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。

## 风险与阻塞

- 当前 `okr_credit_allowed=true` 的允许条件已经被写清，但本轮没有新增真实/准现场 mission artifact 去真正消费这条正向路径。
- O5/O6/O7 最近多轮积累了不少 support-only software proof，虽然这轮已经止住继续加分，但下一轮如果仍拿不到真实或准现场材料，会继续卡在同一 mission evidence blocker。
- O1 真实硬件 lane 仍独立受限于 WAVE ROVER L/R 非零反馈、轮速方向和 HIL 材料。

## 下一轮建议

1. O5/O6 优先拿真实 production cloud、production DB/queue external probe、真实 live endpoint evidence 中至少一类，同一 `task_id` 下触发真正的 `mission_artifact_delta`。
2. O7 若外部云材料仍不可得，就直接消费真实或准现场 same-task materials：`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、live route execution、delivery record、operator confirmation。
3. 在没有新 mission artifact delta 前，O5/O6/O7 后续 sprint 只能算回归守护或 support-only 硬化，不再提高百分比。
