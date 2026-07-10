# O5 Production Cutover Readiness Packet Tech Plan

## sprint_type

sprint_type: epic

## 目标

新增 O5 production cutover readiness packet/readback 合同，把 cutover/drain、migration rehearsal、DB/queue external probe、public ingress/TLS、OSS/CDN live probe、4G/SIM、browser/phone acceptance 等证据状态聚合成可回读、可脱敏、可 fail-closed 的产品 gate。输出必须包含 `okr_credit_allowed`、`support_only_reason`、`next_live_command` 和固定 false safety flags。本 planning 阶段只写计划，不修改产品代码。

## 用户价值和产品北极星

用户需要的不是开发环境里 endpoint 能被 curl 到，而是真实 4G/公网云中转上线前的可解释 readiness：手机能不能访问公网 API、机器人能不能 outbound polling、DB/queue/worker 是否足够生产化、OSS/CDN 是否能承载诊断对象、出问题时用户和运营该执行哪条命令。该 packet 让 O5 的下一步从“重复 probe”变成“对 production cutover 缺口逐项补证”。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 O5，约 85%。
2. 本 sprint 针对最低 Objective O5。
3. 本 sprint 不再推进本地 local probe wrapper，而是推进 O5 `production cutover` readiness packet/readback 合同。
4. 理由：
   - `2026.07.10_08-14_same_task_mission_artifact_credit_gate` 已明确 `okr_credit_allowed=false` 的 support-only probe/readback/checklist 不再计主 OKR 增量。
   - O5 当前缺口是 production DB/queue、public ingress/TLS、4G/SIM、production worker/cutover、OSS/CDN live traffic 和真实 browser/手机证据。
   - 上一轮 O1 已消费历史真实 same-session wheel feedback material，未连续消费 O5 blocker；本轮回到 O5 最低项是合理路由。

## Owner

- 主责 owner：`robot-software-engineer`
- 执行方式：单线闭环。
- `robot-software-engineer` 负责后续实现、测试、修复、相关 `docs/` 同步和 `tech-done.md`。
- `full-stack-software-engineer` 只在 browser/phone acceptance UI 或 O7 展示需要时做只读咨询或后续独立小任务。
- Product / 主节点只负责验收、side2side_check 和 final 收口，不直接写代码、不运行实现命令、不修改真实云配置。

## 后续 implementation 建议文件范围

建议允许 `robot-software-engineer` 后续修改：

- `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `onboard/scripts/o5_same_task_mission_archive_smoke.py`
- `onboard/tests/test_o5_same_task_mission_archive_smoke.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/tech-done.md`

本 planning 子任务实际允许修改的文件只有本 sprint 的三份计划文档。

## 只读输入材料

- `OKR.md`
- `docs/product/cloud_4g_infrastructure.md`
- `sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/final.md`
- `sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/final.md`
- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/final.md`

## 禁止事项

- 不把 `delivery_success`、`safe_to_control`、`primary_actions_enabled`、`robot_control_executed` 或 `production_cutover_success` 从输入透传成 true。
- 不把 ACK terminal、cutover drain 完成、migration rehearsal 完成或 DB/queue probe 通过写成真实送达成功。
- 不输出 credential-bearing URL、Authorization header、bearer token、DB/queue endpoint、OSS AK/SK、完整 object key、raw response body、本地路径、traceback、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
- 不因为 local/docker/software proof gate ready 就把 `okr_credit_allowed` 置 true。

## 计划任务

### 1. Readiness packet 合同

建议新增 `trashbot.o5.production_cutover_readiness_packet.v1`，字段至少包括：

- `schema`
- `schema_version`
- `task_id`
- `packet_id`
- `status`
- `proof_scope_class`
- `production_external_evidence_classes_consumed`
- `readiness_inputs`
- `readiness_blocked_reasons`
- `okr_credit_allowed`
- `support_only_reason`
- `next_live_command`
- `redaction_status`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `production_cutover_success=false`

`status` 建议只允许：

- `production_cutover_readiness_ready_not_success_proof`
- `production_cutover_readiness_support_only`
- `production_cutover_readiness_blocked_not_proven`

### 2. Evidence classes

`readiness_inputs` 至少覆盖：

- `cutover_drain`：pending/drained count、cursor before/after、terminal ACK summary、idempotency replay、partial drain blocked reason。
- `migration_rehearsal`：schema version before/after、migration rehearsal status、rollback plan status、worker startup status、stale artifact status。
- `db_queue_external_probe`：DB connectivity、queue connectivity、migration check、worker check、ordering、transaction isolation、backup/recovery。
- `public_ingress_tls`：public HTTPS reachability、DNS、TLS validity、reverse proxy forwarding、firewall/443 status。
- `oss_cdn_live_probe`：OSS upload or object ref status、STS/restricted credential mode、CDN origin fetch/read status、object count/hash refs。
- `four_g_sim`：SIM status、robot outbound polling over 4G、cloud API reachable from cellular network、offline degradation state。
- `browser_phone_acceptance`：真实 browser/phone session status、bearer-gated command endpoint status、phone-safe diagnostics status。

每个 class 必须有 `source_type`、`state`、`external_evidence_present`、`safe_summary`、`blocked_reason` 和 `redaction_status`。缺字段、未知 state、unsafe text 或 task mismatch 默认 blocked。

### 3. OKR credit gate

`okr_credit_allowed` 计算规则：

- 默认 `false`。
- 只有至少一个新的真实外部 production evidence class 被消费，且 `redaction_status=passed`，且没有危险 true safety flags，且 task/packet identity 一致，才允许为 `true`。
- local/docker/software proof、配置形态存在、readback-only、checklist-only、旧 probe wrapper、旧 cutover rehearsal wrapper 都必须 `false`。
- `true` 仅代表 O5 production readiness evidence delta，不代表 production cutover success、delivery success、safe-to-control 或 robot control executed。

`support_only_reason` 建议枚举：

- `local_probe_wrapper_only`
- `readback_only_no_external_evidence`
- `config_present_not_externally_proven`
- `missing_public_ingress_tls_external_probe`
- `missing_db_queue_external_probe`
- `missing_oss_cdn_live_probe`
- `missing_4g_sim_outbound_polling`
- `missing_browser_phone_acceptance`
- `migration_or_cutover_rehearsal_only`
- `unsafe_or_unredacted_evidence`
- `task_or_packet_mismatch`

### 4. next_live_command

`next_live_command` 必须给出下一条可执行命令方向，不能只写“等待生产环境”。允许输出枚举化 command id 加安全参数摘要，例如：

- `run_public_ingress_tls_external_probe`
- `run_db_queue_external_probe`
- `run_oss_cdn_live_probe`
- `run_4g_sim_outbound_polling_check`
- `run_browser_phone_acceptance_check`
- `run_cutover_drain_with_external_db_queue`

如果实现选择 CLI 示例，示例不得包含真实 URL、token、连接串或对象 key；只能展示占位参数和 artifact 路径占位。

### 5. Readback 接入

建议新增 O6/readback 摘要 `trashbot.o6.production_cutover_readiness_packet_readback.v1`：

- 支持 archive detail、field evidence、artifact bundle 或 consumer detail 中的 include readback。
- 默认只显示 safe summary、class state、blocked reasons、`okr_credit_allowed`、`support_only_reason`、`next_live_command` 和 false safety flags。
- hostile payload 只降级对应 section，不让 unsafe 内容外泄到顶层。

### 6. 测试与文档

后续 implementation 至少覆盖：

- local/software proof only => `okr_credit_allowed=false`，`support_only_reason=local_probe_wrapper_only` 或 `readback_only_no_external_evidence`。
- config present but no external proof => false。
- one sanitized external public ingress/TLS fixture => readiness evidence delta can be true, but all safety/success flags remain false。
- unsafe token/url/connection string/raw response/path/traceback => blocked and no leak。
- dangerous true input flags => blocked and top-level false flags unchanged。
- task mismatch / packet mismatch => blocked。
- missing required fields => blocked。

必须同步更新 `docs/product/cloud_4g_infrastructure.md` 或对应接口文档，说明该 packet 不证明 production success。由于本子任务禁止改其他文件，该同步留给 implementation owner。

## 验收命令

后续 implementation 必须至少运行：

```bash
python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/scripts/o5_same_task_mission_archive_smoke.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke
git diff --check -- cloud-relay/src/ros2_trashbot_cloud_relay onboard/src/ros2_trashbot_behavior onboard/scripts/o5_same_task_mission_archive_smoke.py onboard/tests/test_o5_same_task_mission_archive_smoke.py docs/product/cloud_4g_infrastructure.md docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet
```

本 planning 阶段验收命令为：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|production cutover|okr_credit_allowed|support_only_reason|next_live_command" sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet
```

## 接口影响

- 新增只读 readiness packet/readback 合同，不改变 `/cmd_vel`、robot control、Nav2、硬件参数或真实控制动作。
- O5/O6 readback 增加 additive section，不破坏既有 `cloud_external_probe`、`cloud_db_queue_external_probe` 和 `same_task_mission_evidence_gate`。
- Product closeout 才能决定是否更新 `OKR.md`；implementation 不能仅凭 packet 生成就上调 O5。

## 证据边界

必须固定：

- `proof_scope_class=production_cutover_readiness_not_success_proof`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `production_cutover_success=false`

不能宣称：

- production cutover success
- delivery success
- safe-to-control
- robot control executed
- HIL/hardware safety
- live Nav2 route execution
- OSS/CDN production traffic success，除非只作为外部 evidence class 的脱敏状态被记录

## 风险和阻塞

- 当前仓库可以规划和本地测试 packet contract，但真实公网、TLS、4G/SIM、production DB/queue、OSS/CDN、browser/phone 材料仍可能不可得。
- 如果后续没有新增真实外部 material，Product 收口应把本 sprint 定为 `support_only` 或 readiness guard，不提高 O5 百分比。
- 如果 packet 聚合过宽，容易把 config-present 或 rehearsal-only 误判为 production-ready；因此 `okr_credit_allowed` 必须默认 false。
- 后续 docs 同步是 implementation owner 必做项；本 planning 子任务因文件范围限制没有直接修改 `docs/`。

