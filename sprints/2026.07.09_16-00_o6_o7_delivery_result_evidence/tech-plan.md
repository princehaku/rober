# O6/O7 Delivery Result Evidence Tech Plan

## Sprint 类型

sprint_type: epic

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O6、O7，并列约 53%。
- 本 sprint 是否针对最低 Objective：是。
- 选择理由：O6/O7 的下一缺口已明确为真实或准现场 delivery record / operator dropoff confirmation。本轮使用 local/mock delivery result evidence contract 先打通软件链路，不重复消费真实硬件、真实云或真实投放场景 blocker。
- final.md 收口时需复核：是否形成同一 `task_id` 的 Algorithm → O6 → O7 delivery result evidence 链路；是否保持所有安全旗标为 false；是否没有把 mock/operator claim 宣称成真实 delivery success。

## 最近两轮 blocker 扫描

- `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/final.md`：完成态，下一步要求 `nav2_goal_result_or_delivery_record`。
- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/final.md`：完成态，下一步要求 delivery record / delivery result 进入同一证据链。
- 结论：没有连续 blocked 的同一根因。本轮不依赖真实串口、真实 production cloud 或真实 delivery scene。

## 新增接口合同

新增 additive 摘要名称：`delivery_result_evidence`。

建议 schema：`trashbot.delivery_result_evidence.v1`。

建议 proof scope：`software_proof_delivery_result_evidence_only`。

最小字段：

- `schema`
- `proof_scope`
- `source`
- `source_schema`
- `status`
- `task_id`
- `task_id_source`
- `record_present`
- `record_read_ok`
- `record_status`
- `delivery_result_claimed`
- `operator_confirmation_present`
- `dropoff_confirmation_type`
- `completed_at_utc`
- `linked_nav2_goal_execution_proven`
- `blocked_reasons`
- `next_required_evidence`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

字段解释：

- `delivery_result_claimed` 只能表示输入记录存在完成/投放声明，不能让 `delivery_success` 变成 true。
- `operator_confirmation_present` 表示人工确认字段存在，仍不代表生产验收完成。
- `linked_nav2_goal_execution_proven` 只从同一 packet 的 Nav2 摘要读取，不重新推断控制成功。
- `completed_at_utc` 只接受短 UTC 文本，不接受路径、URL、token、raw/base64。

## 并行 owner 分工

### Task A - Algorithm / delivery result evidence generator

Owner：`robot-algorithm-engineer`

职责：

- 给 `field_route_evidence_manifest.py` 增加 `--delivery-result-json`。
- 从安全裁剪 JSON 生成 `delivery_result_evidence`，写入 manifest 顶层与 `field_motion_evidence_packet.delivery_result_evidence`。
- 缺输入、JSON 不可读、schema mismatch、危险 true、path/root/token/raw/base64/credential URL 时输出 blocked 摘要。
- 更新导航文档与单元测试。

允许改动范围：

- `/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/tech-done.md`

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

### Task B - O6 archive/readback support

Owner：`robot-software-engineer`

职责：

- 在 O6 field-evidence / artifact-bundle ingest 中接收和白名单 `delivery_result_evidence`。
- 在 archive task detail、field evidence、artifact bundle、consumer detail alias 与 `include=delivery_result_evidence` 中回读。
- 保持 additive，不破坏 `field_motion_evidence_packet`、`nav2_goal_execution_evidence`、artifact access probe、offline seed smoke、route-root seed gate。
- 更新 O6 API 文档与单元测试。

允许改动范围：

- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/tech-done.md`

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

### Task C - O7 consumer/UI support

Owner：`full-stack-software-engineer`

职责：

- 在 O7 consumer adapter 中请求/读取 `delivery_result_evidence`。
- 在 shared contracts 和 O7 fixture preview UI 中展示 delivery result readiness、blocked reasons、next evidence 和 false safety fields。
- 将 delivery result evidence 汇总进 artifact bundle readiness，不打开任何 submit/control/action。
- 更新 PC 文档和 Vitest 覆盖。

允许改动范围：

- `/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`
- `/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/tech-done.md`

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

### Task D - Product 收口

Owner：`product-okr-owner`

职责：

- Engineer 完成后核对三个验证结果和证据边界。
- 更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 必要时保守更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，不归档 KR，除非证据达到 KR 完成条件。

允许改动范围：

- `/Users/m1/apps/rober/OKR.md`
- `/Users/m1/apps/rober/docs/process/okr_progress_log.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/tech-done.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/side2side_check.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/final.md`

验收命令：

```bash
rg -n "delivery_result_evidence|software_proof_delivery_result_evidence_only|O6|O7|safe_to_control: false|delivery_success: false" sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence OKR.md docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence
```

## 全局安全边界

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

任何新增路径都不得回显绝对路径、root、token、credential URL、raw payload、base64、串口路径、`/cmd_vel` 或真实控制成功声明。

## 最终验收命令

Engineer 验证完成后，Product 或对应 owner 需确认：

```bash
git diff --check
```

