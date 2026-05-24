# Cloud Command Lifecycle Support Handoff Owner Response Intake Tech Plan

Run time: 2026-05-24 10:11 Asia/Shanghai

## 目标

实现 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake`，把上一轮 support handoff bundle 的 safe copy、pending-safe command/evidence、`owner_handoff` 和 `next_required_evidence` 接入一个 fail-closed owner/support response intake。

本轮证据边界固定为：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate
```

必须保留 false-state flags：

```text
not_proven
delivery_success=false
primary_actions_enabled=false
safe_to_control=false
```

必须明确：

- no OKR percentage lift
- not true phone/browser proof
- not public HTTPS/TLS
- not 4G/SIM
- not OSS/CDN live traffic
- not production DB/queue
- not worker/cutover
- not verified terminal result
- not HIL
- not PR #5 resolved
- not delivery success

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5。
3. 选择理由：最新 sprint `2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle` 已完成 support handoff bundle，但 Objective 5 因缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result 而 no OKR percentage lift。本机只有 Docker，没有真实硬件、真实手机、真实公网云或 4G/SIM，因此本轮只推进下一条安全 owner/support response intake，不宣称真实 O5 完成度提升。
4. PR evidence：PR #5 已 merge/closed，但 review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；PR #7 open 但无 review threads/comments，主题是目录/测试/子 Agent 分层规则，不改变本轮 O5 owner response intake 的优先级。

## 并行 owner 任务

后续 implementation sprint 默认在同一轮并行启动 3 个 owner 任务。文件范围互不重叠；若 Robot/API consultation 发现无需代码改动，Task B 只返回 read-only 结论和现有证据，不写文件。

### Task A: Full-Stack mobile panel / fixture / docs

责任 Engineer：User Touchpoint Full-Stack Engineer。

目标：

- 在 `mobile/web` 增加只读 owner response intake panel。
- 读取 `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_summary` 或兼容 safe summary。
- 展示 safe command id、safe `evidence_ref`、owner/support response status、accepted/missing/rejected/unsafe/blocked 分类、`owner_handoff`、`next_required_evidence`、safe copy、proof boundary 和 false-state flags。
- Start Delivery、Confirm Dropoff、Cancel 保持 disabled，不新增 replay/resubmit、ACK/cursor、review mutation、material upload、GitHub mutation 或 robot control path。

允许文件范围：

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake.json`
- `docs/product/mobile_user_flow.md`

禁止范围：

- `onboard/`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- 其他 sprint 目录
- 任何真实 credential、token、signed URL、local path、raw artifact 或硬件参数

验收命令：

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake.json >/tmp/cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake.json docs/product/mobile_user_flow.md
```

### Task B: Robot/API diagnostics safe alias or compatibility consultation

责任 Engineer：Robot Platform Engineer。

目标：

- 先 read-only 检查上一轮 HTTP export/support handoff bundle 是否已有足够 safe fields：safe copy、pending-safe command/evidence、`owner_handoff`、`next_required_evidence`、`redaction_status=passed`、`accepted_processing_only_not_delivery_success`、`terminal_result_pending`、false-state flags。
- 如果已有字段足够，返回 "Robot/API changed none" 与证据，不改代码。
- 如果缺少 mobile/support 兼容 alias，新增只读 diagnostics/status safe alias，不新增控制路径、ACK/cursor mutation、replay/resubmit、material upload、GitHub mutation 或 robot command route。

允许文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/remote_4g_mvp.md`

禁止范围：

- `mobile/web/`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- 其他 sprint 目录
- WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数、serial devices、baudrate、`/cmd_vel` 暴露或真实硬件配置

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not HIL|not PR #5 resolved" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md
```

### Task C: Product closeout / OKR boundary

责任 Engineer：Product Manager / OKR Owner。

目标：

- 实现和验证完成后，更新 sprint 留档链路。
- 若 durable implementation landed，更新 `OKR.md` 4.1 和 `docs/process/okr_progress_log.md`，但 Objective 5 保持约 68%，no OKR percentage lift。
- 明确 PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`。
- 明确本轮不是 true phone/browser proof、public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、verified terminal result、HIL、PR #5 resolved 或 delivery success。

允许文件范围：

- `sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/tech-done.md`
- `sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/side2side_check.md`
- `sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

禁止范围：

- 产品代码
- 测试代码
- 硬件配置
- 其他 sprint 目录

验收命令：

```bash
test -f sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/tech-done.md && test -f sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/side2side_check.md && test -f sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/final.md
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not true phone/browser proof|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/tech-done.md sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/side2side_check.md sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/final.md
```

## 集成顺序

1. Task B 先以 read-only 判断 Robot/API 是否需要 code compatibility；若需改，只能做 safe alias。
2. Task A 并行实现 mobile/support panel，并用 fixture 覆盖 accepted/missing/rejected/unsafe/blocked 至少一个主路径和一个 fail-closed 路径。
3. Task C 等 Task A/B evidence 返回后做 closeout，不把 Docker/local proof 写成 OKR percentage lift。

## 证据边界

唯一允许证据边界：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate
```

禁止宣称：

- external cloud proof
- true phone/browser proof
- public HTTPS/TLS
- 4G/SIM
- OSS/CDN live traffic
- production DB/queue
- worker/cutover
- verified terminal result
- HIL
- PR #5 resolved
- delivery success

## 当前 planning 验收命令

本 planning run 只验证三份 planning 文档存在、关键边界齐全、无 scoped whitespace error：

```bash
test -f sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/pre_start.md && test -f sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/prd.md && test -f sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/tech-plan.md
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not true phone/browser proof|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake
git diff --check -- sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/pre_start.md sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/prd.md sprints/2026.05.24_10-11_cloud-command-lifecycle-support-handoff-owner-response-intake/tech-plan.md
```
