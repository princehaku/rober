# Cloud Command Lifecycle Acceptance HTTP Export Tech Plan

Run time: 2026-05-24 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 技术目标

实现 `cloud_command_lifecycle_replay_acceptance_packet_http_export`：在 independent cloud relay 暴露只读 HTTP GET API，读取与上一轮 CLI export 同源的安全验收包，并返回 support/field-owner 可用的 phone-safe JSON。

目标 route：

```text
GET /api/support/cloud-command-lifecycle-replay-acceptance-packet-export
```

目标 evidence boundary：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate
```

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 是否针对最低 Objective：是。本轮直接推进 Objective 5 的 independent cloud relay support HTTP API surface。
3. 不提升百分比的理由：本轮只做 Docker/local read-only support API proof；缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、true phone/browser proof、verified terminal result、HIL、Nav2/fixed-route runtime 和 delivery success。因此计划默认 no OKR percentage lift。

## 文件范围与 owner

### Task A - Full-Stack HTTP Export

Owner：`full-stack-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- 本 sprint `tech-done.md` 中 Task A 结果段

说明：

- `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py` 当前只是 thin wrapper；只有需要补 wrapper docs marker 时才允许改动该文件。
- 实际 `make_handler`、`/api/status`、HTTP route 和 CLI export builder 均在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`。
- focused HTTP tests 使用 `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`；不得引用不存在的 `cloud-relay/tests/`。

要求：

- 新增只读 GET route。
- 返回 `cloud_command_lifecycle_replay_acceptance_packet_http_export` payload。
- 保留 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`。
- 保留源 acceptance packet / CLI export boundary 说明。
- 保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 不要求 bearer auth也可以；如果复用现有 bearer middleware，必须不泄露 token。
- 不 replay/resubmit command、不 post ACK、不 mutate cursor/state、不上传材料、不触发 GitHub action、不控制 Nav2/机器人、不写 delivery success。

验收命令建议：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m pytest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k "cloud_command_lifecycle_replay_acceptance_packet_http_export or support"
rg -n "cloud_command_lifecycle_replay_acceptance_packet_http_export|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate|accepted_processing_only_not_delivery_success|delivery_success.*false|primary_actions_enabled.*false|safe_to_control.*false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/tech-done.md
```

### Task B - Robot Safe-Alias Boundary Check

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/` 中与 `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary` 直接相关的文件，仅在 safe alias 缺必要字段时才改。
- `docs/product/cloud_4g_infrastructure.md` 或相关 docs 中 Robot diagnostics 消费边界段，仅在需要时补充。
- 本 sprint `tech-done.md` 中 Task B 结果段。

要求：

- 优先只读核对；如果现有 Robot diagnostics contract 已足够，changed files 可以为空。
- 确认 Robot side 不启用 ACK post、cursor mutation、command replay、material upload、GitHub action、Nav2、HIL、UART、WAVE ROVER 或 delivery success。
- 确认 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending` 的边界没有被 O5 HTTP export 改写。

验收命令建议：

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet|robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary|delivery_success|primary_actions_enabled|safe_to_control|PRRT_kwDOSWB9286CJ3tX" onboard/src/ros2_trashbot_behavior docs/product
git diff --check -- onboard/src/ros2_trashbot_behavior docs/product/cloud_4g_infrastructure.md
```

### Task C - Product Closeout

Owner：`product-okr-owner`

允许改动：

- `sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/tech-done.md`
- `sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/side2side_check.md`
- `sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 汇总 Task A / Task B 的实际改动和验证输出。
- 如果只有 Docker/local HTTP export proof，`OKR.md` Objective 5 保守保持约 68%，写明 no OKR percentage lift。
- Closeout 必须显式保留 `not true phone/browser proof`、`not delivery success`、`not HIL`、`not PR #5 resolved`、`PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。

验收命令建议：

```bash
test -f sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/tech-done.md && test -f sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/side2side_check.md && test -f sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export/final.md
rg -n "cloud_command_lifecycle_replay_acceptance_packet_http_export|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate|Objective 5|not true phone/browser proof|no OKR percentage lift|not delivery success|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending" sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export OKR.md docs/process/okr_progress_log.md
```

## 并行启动要求

本轮是 2+ owner Epic sprint，文件范围基本不重叠：

- `full-stack-software-engineer` 可先实现 HTTP route 和 tests。
- `robot-software-engineer` 可并行做 Robot safe-alias read-only 核对。
- `product-okr-owner` 等 Task A / B 返回后再做 closeout 和 OKR 保守更新。

主节点不得自己写产品代码、测试代码或运行实现验证命令；实现和验证必须由对应子 agent 执行。主节点只做派发、等待、证据核对、sprint 文档收口和最终汇总。

## 接口影响

新增只读 route：

```text
GET /api/support/cloud-command-lifecycle-replay-acceptance-packet-export
```

响应必须是 JSON，推荐包含：

- `schema`
- `schema_version`
- `capability=cloud_command_lifecycle_replay_acceptance_packet_http_export`
- `evidence_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`
- `source_boundary`
- `safe_command_id`
- `safe_evidence_ref`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `terminal_result_status=terminal_result_pending`
- `owner_handoff`
- `next_required_evidence`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `redaction_status=passed`

响应不得包含：

- bearer token / Authorization header / signed URL / credential-bearing URL。
- DB/queue endpoint、OSS AK/SK、root password。
- local state path、traceback、raw artifact path。
- ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER details。
- raw command replay material、raw ACK mutation material、raw GitHub mutation payload。

## 验证围栏

只跑 fenced validation：

- `py_compile` for changed Python.
- focused pytest for the new HTTP route and no-side-effect checks.
- focused `rg` for required markers and forbidden overclaim markers.
- scoped `git diff --check` for touched files.

不跑 broad regression，除非 focused tests 暴露接口破坏。

## 风险与阻塞

- 本轮不解决 production auth、public HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic。
- 本轮不证明 true phone/browser proof，也不证明 production app 或 PWA prompt。
- 本轮不证明 verified terminal delivery/dropoff/cancel result、Nav2/fixed-route runtime pass、route/elevator field pass、HIL、WAVE ROVER/UART 或 delivery success。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；本轮 HTTP export 不得声明 PR #5 resolved。

## 完成定义

- 三类 owner 结果都写入 `tech-done.md`。
- `side2side_check.md` 对照 PRD 验收 P0/P1/P2。
- `final.md` 写清 Objective 5 movement、no OKR percentage lift、证据边界和剩余外部缺口。
- 如代码/docs 有 durable change，按用户要求提交并推送远程。
