# Same-Task Mission Artifact Credit Gate Tech Done

## sprint_type

epic

## Robot Algorithm / O5-O7 Gate Source

### 实际改动

- `onboard/scripts/field_route_evidence_manifest.py`
  - 为 `same_task_mission_evidence_gate` 新增结构化 `mission_artifact_delta` 判定字段：`same_task_id_consumed`、`live_or_field_command_executed`、`support_only_reason`、`okr_credit_allowed`。
  - 把 `same_task_id`、live/field mission artifact 消费和 support-only 原因拆开表达，避免 probe-only、checklist-only、readback-only 输入继续被误记为主 OKR 进度。
  - 保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，没有把 credit gate 误写成控制许可。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 增加 ready gate 下 `okr_credit_allowed=true` 的正例。
  - 增加 probe/checklist/readback-only/support-only 输入下 `okr_credit_allowed=false` 的反例，覆盖 fail-closed 路径。
- `docs/navigation/route_evidence_manifest.md`
  - 记录 `same_task_mission_evidence_gate` 新增 credit gate 合同字段和 fail-closed 语义，明确 `okr_credit_allowed=false` 只代表 support-only，不代表 mission success。

### 验证结果

- `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
  - 结果：通过，无输出
- `python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
  - 结果：`Ran 60 tests in 0.313s OK`
- `git diff --check`
  - 结果：通过，无 whitespace / conflict 标记问题

### 失败定位与修复

- 本轮未记录新的返工失败；worker 直接在结构化 `mission_artifact_delta` 合同上补齐了 credit gate 字段和回归测试。

### 剩余风险

- `okr_credit_allowed=true` 的正例当前仍是软件合同和受控 fixture 证明，不是新的真实 production cloud、真实 live route execution、真实 delivery record 或真实 operator confirmation。
- 后续如果上游新增 mission artifact 类型，但没有同步进入 `mission_artifact_delta` 结构化判定，仍可能出现“材料已到但 credit gate 未放行”的保守 false negative。

## Robot Software / O6 Archive Readback

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - O6 兼容 legacy 字符串和结构化 `mission_artifact_delta`，但只有结构化 credit fields 才允许进入 credit 判断。
  - 在 archive detail、field evidence、consumer detail 和 include 回读中保留 `same_task_id_consumed`、`live_or_field_command_executed`、`support_only_reason`、`okr_credit_allowed`。
  - 对 support-only、缺字段、legacy unstructured delta、unsafe text、dangerous true 和 task mismatch 全部 fail-closed，继续输出 `okr_credit_allowed=false`。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 增加一组 credit-allowed 正例和多组 support-only / blocked 反例。
  - 覆盖 archive detail、consumer include 和 readback alias 的 credit fields 保留逻辑。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 补充 O6 same-task mission gate readback 的 credit fields 合同，以及 support-only / 缺字段时的 fail-closed 约束。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 结果：通过，无输出
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 结果：`Ran 168 tests in 64.612s OK`
- `git diff --check`
  - 结果：通过，无 whitespace / conflict 标记问题

### 失败定位与修复

- 本轮未记录新的返工失败；worker 已把 legacy 字符串 delta 保持兼容读取，但在 credit 判定上收紧为 fail-closed。

### 剩余风险

- O6 现在只证明 archive/readback 能正确传递 credit gate 字段，不证明真实 production cloud、真实生产 DB/queue、真实隧道、真实 live route execution 或真实 delivery success。
- 当前仍需同时维护 legacy 字符串和结构化对象兼容路径；后续如果长期保留双轨合同，回归面会继续扩大。

## Full-stack / O7

### 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 为 `same_task_mission_evidence_gate` 增加 O6 credit gate 字段：`same_task_id_consumed`、`live_or_field_command_executed`、`support_only_reason`、`okr_credit_allowed`。
  - 为 `same_task_mission_material_checklist` 复用同一组 credit gate 字段，避免 operator 只能回看 gate 原始摘要。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 兼容旧 `mission_artifact_delta` 字符串和新结构化对象。
  - 读取并校验 O6 credit fields；缺字段时 fail-closed。
  - 当 `okr_credit_allowed=false` 时，把 support-only 原因保留到 gate/checklist 摘要与 blocker 中，并把 checklist 总状态收紧为 `blocked_not_proven`，避免把材料 ready 误读成可计 OKR 主进度。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 在 same-task gate 摘要中展示 `okr_credit_allowed`、`support_only_reason`、`same_task_id_consumed`、`live_or_field_command_executed`。
  - 在 checklist 摘要中同步展示 credit gate 字段，并明确 `okr_credit_allowed=false` 时仍是 support-only/blocked 语义。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 O7 consumer read contract fixture 和断言，覆盖 credit gate 字段与 support-only fail-closed 语义。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 UI fixture 和断言，确保面板展示 credit gate 字段，且 checklist 不再把 support-only 输入显示为 `materials_ready_not_success_proof`。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 补充 O7 consumer detail 对 O6 credit fields 的消费要求，以及 `okr_credit_allowed=false` 时的 UI 语义约束。

### 验证结果

- `cd pc-tools/workstation && npm run test`
  - 结果：`Test Files  3 passed (3)` / `Tests  484 passed (484)`
- `cd pc-tools/workstation && npm run build`
  - 结果：`✓ built in 1.78s`
  - 备注：保留既有 Vite warning：`Some chunks are larger than 500 kB after minification`
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过，无报错
- `git diff --check`
  - 结果：通过，无 whitespace / conflict 标记问题

### 失败定位与修复

- 首轮测试失败 1：
  - 现象：旧断言仍把 `same_task_mission_material_checklist.status` 视为 `materials_ready_not_success_proof`
  - 根因：本轮 credit gate 规则要求 `okr_credit_allowed=false` 时 checklist 保持 support-only/blocked 语义
  - 修复：更新 contract fixture、adapter 逻辑和 catalog/UI 断言为 `blocked_not_proven`
- 首轮测试失败 2：
  - 现象：UI 断言匹配旧的 summary 文本
  - 根因：新增 credit gate 展示后，same-task checklist 的可见文本形态发生变化
  - 修复：断言改为匹配新的 blocked/status 与 credit gate 字段展示

### 剩余风险

- 本轮只证明 O7 已消费并展示 O6 credit gate 字段，不证明真实 production cloud、真实 live route execution、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 当前 fixture/contract 仍是 local/mock software proof；若 O6 上游后续再调整 credit gate 字段名或 status 语义，O7 需要同步回归。
- `npm run build` 仍有既有 chunk-size warning；本轮未处理打包拆分，因为与 same-task credit gate 目标无关。

## Product Closeout

### 汇总结论

- Algorithm、O6、O7 三个 worker 的软件合同已经串起来：同一 `task_id` 的 mission gate 现在能显式区分“消费了 live/field mission artifact”与“只是 support-only 守护”。
- 本轮产物属于 hard gate / credit gate 软件合同，不新增真实 production cloud、真实 live route execution、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 因此本轮 `okr_credit_allowed=false` 仍是主流场景，O5/O6/O7 百分比保持约 `85%/85%/85%` 不变；本轮不再把 wrapper、probe、checklist 或 readback-only 进展记成主 OKR 增量。

### Product 文档改动

- 回填本文件，补齐 Algorithm / O6 / O7 三段，消除并行写覆盖。
- 新建 `side2side_check.md` 和 `final.md`。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`，把本轮定性为 support-only credit gate 硬化，不上调 O5/O6/O7 百分比。
