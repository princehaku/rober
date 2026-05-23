# Cloud Command Lifecycle Acceptance Docker Smoke Proof Tech Done

Run time: 2026-05-24 05:16 Asia/Shanghai

## Sprint Type

sprint_type: epic

## User Value And Product North Star

用户价值：support reviewer 和 field owner 可以把 `cloud-relay/scripts/docker_smoke.sh` 当作 cloud-relay Docker/local deploy-smoke freshness proof，确认已落地的 `cloud_command_lifecycle_replay_acceptance_packet` 没有从部署证明链路中退化。

产品北极星保持不变：普通手机用户通过云中转操作低成本垃圾投递机器人，support 能看懂 ACK / terminal-result pending / owner handoff / next evidence，但不会暴露 raw control、ROS topic、UART、WAVE ROVER 或任何控制授权。

## OKR Mapping

- Primary Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，仍是最低项，约 68%。
- KR 对齐：O5 KR1 command/status/ACK 契约 freshness；O5 KR6 graceful degradation / support diagnostics 边界。
- 进度判定：本轮是 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`，只证明 Docker/local deploy-smoke 能复核 acceptance packet；no OKR percentage lift。

## Task A - Full-Stack Result

Changed files:

- `cloud-relay/scripts/docker_smoke.sh`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`

实际改动：

- 在 `cloud-relay/scripts/docker_smoke.sh` 增加 `cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_proof` section。
- Docker relay 容器内复用 Robot/API 的 `build_cloud_command_lifecycle_audit_export`、`build_cloud_command_lifecycle_replay_drill`、`build_cloud_command_lifecycle_replay_acceptance_packet` 构建同一 acceptance packet。
- 新增 wrapper boundary：`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`。
- 保留 source packet boundary：`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`。
- 显式保留 `accepted_processing_only_not_delivery_success`、`terminal_result_pending`、`owner_handoff`、`next_required_evidence`、`delivery_success=False`、`primary_actions_enabled=False`、`safe_to_control=False`。
- 在 `cloud-relay/README.md` 和 `docs/product/remote_4g_mvp.md` 同步说明该 smoke 不是 true phone/browser proof、not production DB/queue、not worker/cutover、not HIL、not delivery success，且 no OKR percentage lift。

Task A validation accepted from worker:

```text
bash -n cloud-relay/scripts/docker_smoke.sh: pass
required rg: pass
git diff --check -- cloud-relay/scripts/docker_smoke.sh cloud-relay/README.md docs/product/remote_4g_mvp.md: pass
bash cloud-relay/scripts/docker_smoke.sh: exit 0, container built, smoke ran, cleanup completed
```

Focused artifact snippet accepted:

```text
capability cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_proof
smoke_boundary software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate
packet_boundary software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate
ack_semantics accepted_processing_only_not_delivery_success
terminal_result_status pending_verified_terminal_result_not_proven
delivery_success False
primary_actions_enabled False
safe_to_control False
proof_boundary_copy ... not true phone/browser proof; no OKR percentage lift
```

## Task B - Robot Consultation Result

Changed files: none.

Robot/API diagnostics conclusion:

- Existing Robot/API diagnostics already expose `cloud_command_lifecycle_replay_acceptance_packet`.
- Existing safe alias remains `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary`.
- Packet remains read-only metadata.
- Packet cannot replay commands, post ACKs, mutate cursors, upload materials, run GitHub actions, trigger Nav2, touch WAVE ROVER, use UART, prove HIL, authorize control, or claim delivery success.

Task B validation accepted from worker:

```text
required rg found markers across docs/interfaces/operator_gateway_diagnostics.md, docs/product/remote_4g_mvp.md, operator_gateway_diagnostics.py, and test_operator_gateway_diagnostics.py
git diff --check for scoped Robot files: pass
scoped git status --short -- scoped Robot files: no output
py_compile / unittest: not run because Robot changed no files
```

## Task C - Product Closeout Work

Created / updated:

- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/tech-done.md`
- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/side2side_check.md`
- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Product judgment:

- Objective 5 remains about 68%.
- Objective 1 remains about 81%; PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`.
- Objectives 2/3/4 remain about 99%.
- This is Docker/local software proof only. It is not true phone/browser proof, not real external cloud proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not verified terminal result, not HIL, not WAVE ROVER/UART proof, not PR #5 resolution, not route/elevator field pass, and not delivery success.

## Validation To Carry Into Final

Required closeout validation to run after Product edits:

```bash
test -f sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/tech-done.md && test -f sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/side2side_check.md && test -f sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/final.md
rg -n "cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_proof|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not true phone/browser proof|no OKR percentage lift|not production DB/queue|not worker/cutover|not HIL|not delivery success" sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof OKR.md docs/process/okr_progress_log.md cloud-relay/scripts/docker_smoke.sh cloud-relay/README.md docs/product/remote_4g_mvp.md
```

## Remaining Risk

- Docker smoke pass remains Docker/local software proof, not production DB/queue or public cloud proof.
- No true phone/browser proof was run in this sprint.
- No HIL, WAVE ROVER/UART, LiDAR/ToF installation, route/elevator field pass, verified terminal result, or delivery success evidence was introduced.
- Product did not run a whole-repo Chinese technical-comment ratio audit; Task A edited a shell smoke script and docs, and the touched shell section uses Chinese explanatory comments around the new logic.
