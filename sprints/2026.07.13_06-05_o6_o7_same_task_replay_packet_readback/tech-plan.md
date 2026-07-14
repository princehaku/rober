# Tech Plan - O6/O7 Same-Task Replay Packet Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o6_o7_same_task_replay_packet_readback_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节数字完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 不针对 O5，转向 O6/O7，二者约 `93%`。
3. 不针对 O5 的理由：O5 最近多轮已确认缺真实 production/external evidence，继续做 readiness、handoff、cutover packet 或 support-only wrapper 不会产生新的真实外部证据，也会违反同一 blocker 重复消费红线。
4. 选择 O6/O7 的理由：05:02 same-task replay packet 是新的同任务材料，且明确尚未进入 O6 archive/readback 或 O7 consumer detail。本轮能消费该 packet 到 local/mock readback 与 PC consumer，属于新的 same-task material consumption，而不是 O5 support-only 包装。
5. 收口要求：若后续实现只产生展示文案或 wrapper，而没有 O6 readback + O7 consumer detail 测试证据，final 必须判定为未达成本 sprint。

## 输入证据

权威输入：

- Source summary: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json`
- Source packet JSONL: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_route_replay_packet.jsonl`
- Product closeout: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/final.md`

必须保留的 identity：

- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_identity_verified=true`
- `same_task_replay_packet_ready=true`

必须保留的 false fields：

- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `primary_actions_enabled=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `connects_cloud_production=false`

## 技术方案

### O6 local/mock archive/readback

Full-stack owner 应优先复用 `remote_cloud_relay.py` 现有 O6 file-backed store 与 consumer read API。

实现可选两种方案，但必须在 `tech-done.md` 写清实际选择：

- 方案 A：新增 dedicated section，例如 `same_task_replay_packet_readback`，schema 可命名为 `trashbot.o6.same_task_replay_packet_readback.v1`。该方案语义最清楚，避免和 route execution material packet 混淆。
- 方案 B：在既有 same-task material/readback section 中新增明确子字段，字段名必须包含 `replay_packet`，且状态必须是 ready-not-execution-proof，不能复用会让人误读的 execution success 字段。

O6 回读内容只允许白名单摘要：

- packet id、task id、route intent id
- source schema 和 proof boundary
- route/replay/source summary basename refs
- route CSV row count、replay JSONL event count、structured pose count
- sha256 prefix，不回显完整路径以外的本地绝对路径、raw/base64、token、credential URL
- `blocked_reasons`
- `next_required_evidence`
- fixed false safety fields

### O6 consumer detail

`GET /api/o6/consumer/tasks/<task_id>` 必须能通过 include 或默认 detail 返回 packet readback。

建议 include 名称：

- `include=same_task_replay_packet_readback`

如果不新增 include 名称，而是复用现有 include，必须在 tests 中证明：

- selected `task_id` 被保留；
- packet identity 可在 top-level detail 或 field_evidence/artifact_bundle wrapper 中稳定读取；
- 缺包时返回 `blocked_not_proven`，不是 success-like null。

### O7 PC consumer detail

`pc-tools/workstation` 应通过 O6 consumer detail 主路径读取，不直接读取本地 source packet 绝对路径。

O7 输出要求：

- consumer detail adapter 保留 `task_id`、`packet_id`、`route_intent_id`、counts、source refs、blocked reasons、next evidence。
- UI 可在 consumer detail / fixture preview 的 O6/O7 证据区域展示 readback-only 摘要。
- 默认首屏普通用户视图不得出现工程词；若展示在普通控制台，必须放入默认关闭的高级诊断。
- `O7FixturePreviewPanel.vue` 或对应 detail 组件只做只读展示，不触发 probe、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 后续 full-stack owner 文件范围

允许后续 full-stack owner 修改的建议范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/**/*.test.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/src/components/**/*.test.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/tech-done.md`

范围外默认不得修改。若实现发现必须新增 fixture，可放在 `pc-tools/workstation/src/**/__fixtures__/` 或既有测试 fixture 目录，并在 `tech-done.md` 写清理由。

## 接口影响

- O6 API：可能新增 `same_task_replay_packet_readback` include 或在现有 consumer detail 中新增同名 section。
- O6 archive/store：只新增 local/mock file-backed safe summary，不连接真实 cloud DB/queue/OSS，不改变 production endpoints。
- O7 adapter：新增或扩展对 O6 consumer detail packet readback 的 fail-closed 解析。
- O7 UI：新增只读展示或 detail section，不改变控制按钮、不新增 motion endpoint。
- Docs：同步说明本 section 是 readback-only software proof，不是 route execution 或 delivery proof。

兼容要求：

- O6/O7 缺该 section 时必须返回或显示 `blocked_not_proven`。
- unsafe path/url/token/raw/base64/traceback/response body 必须 fail-closed。
- dangerous true 字段必须 fail-closed 或固定 false，不允许透传为 ready。
- `task_id` 不得因 section 缺失或 task mismatch 被替换成默认值。

## 验收命令

后续 full-stack owner 必须运行并记录：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/interfaces/o6_cloud_archive_api.md \
  pc-tools/workstation \
  docs/product/pc_tools_workstation.md \
  sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback
```

后续 owner 还必须补充至少一个结构化断言或 targeted test，覆盖：

- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_replay_packet_ready=true`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`

Product planning 本轮只运行：

```bash
git diff --check -- sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback
```

## 验收标准

通过标准：

- O6 和 O7 测试全部通过。
- O6 consumer detail 能稳定回读 packet readback。
- O7 consumer detail 能展示 packet readback，并保持 fail-closed safety flags。
- 文档同步说明 readback-only / local-mock / software-proof 边界。
- Sprint `tech-done.md` 记录实际改动、验证输出、失败定位和剩余风险。

不通过标准：

- 只有文案或 checklist，没有 O6 archive/readback 测试。
- 将 05:02 packet 表述为 route execution、delivery proof、HIL 或 safe-to-control。
- 透传绝对路径、token、credential URL、raw/base64 或危险 true 字段。
- O7 页面默认首屏暴露工程词或误导普通用户可发车。

## 风险和回滚边界

- 只读 readback section 可以安全回滚，不应影响既有 O6 archive endpoints。
- 若新增 include 会扩大 O6/O7 fixture 面，必须补缺包和 unsafe payload 的 negative tests。
- 若发现 05:02 source artifact 字段不足，不要现场补造执行材料；应 fail-closed 并要求 Algorithm 另开 source artifact 修复 sprint。

## 后续收口要求

`tech-done.md` 必须包含：

- 实际改动文件列表。
- O6/O7 接口或 UI 的最终实现方式。
- 验收命令输出片段。
- 失败定位和修复记录。
- 剩余风险。
- OKR 影响判断，明确是否仍不归档 KR。

`side2side_check.md` 必须对照本 PRD 和 tech-plan 做验收。`final.md` 必须明确 Product 是否接受 O6/O7 readback 增量，以及不得声明的能力。
