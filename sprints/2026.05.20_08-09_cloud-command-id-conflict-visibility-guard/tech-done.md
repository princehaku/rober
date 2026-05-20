# Sprint 2026.05.20_08-09 Cloud Command ID Conflict Visibility Guard - Tech Done

## 1. 迭代声明

- sprint_type: epic
- 主题：`cloud_command_id_conflict_visibility_guard`
- 证据边界：`software_proof_docker_cloud_command_id_conflict_visibility_guard`
- closeout owner：`product-okr-owner`

## 2. 实际改动

Robot worker 完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/remote_4g_mvp.md`

Robot 结果：

- canonical command identity 基于 `type` + sorted JSON `payload`，避免 raw JSON 字段顺序造成误判。
- 同内容 duplicate 仍按 cached ACK dedupe。
- 同一 `command.id` 但 `type` 或 `payload` 不一致时输出 `command_id_conflict`，拒绝执行，不复用 cached ACK，不把 ACK 写成 delivery success。
- `primary_actions_enabled=false` 保持，优先级为 pending ACK、expired command、conflict、same-content duplicate。

Full-Stack worker 完成：

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_id_conflict_visibility_guard.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Full-Stack 结果：

- mobile/web 消费 `degradation_state=command_id_conflict` 和 `proof_boundary=software_proof_docker_cloud_command_id_conflict_visibility_guard`。
- 手机端中文展示“命令 ID 冲突；机器人已拒绝执行；这不是送达成功。”。
- Start Delivery / Confirm Dropoff / Cancel 保持 disabled。
- 不新增 replay、resubmit、ACK、cursor endpoint 或控制面副作用。

Product closeout 完成：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_08-09_cloud-command-id-conflict-visibility-guard/tech-done.md`
- `sprints/2026.05.20_08-09_cloud-command-id-conflict-visibility-guard/side2side_check.md`
- `sprints/2026.05.20_08-09_cloud-command-id-conflict-visibility-guard/final.md`

## 3. 验证结果

Engineer 已回传围栏：

- Robot unittest：`Ran 401 tests in 93.649s OK`
- Robot `py_compile`：exit 0
- Robot required `rg`：exit 0
- Robot scoped `git diff --check`：exit 0
- Full-Stack unittest：`Ran 155 tests in 0.990s OK`
- `node --check mobile/web/app.js`：exit 0
- Full-Stack required `rg`：exit 0
- Full-Stack scoped `git diff --check`：exit 0

Product closeout 需复跑：

```bash
rg -n "cloud_command_id_conflict_visibility_guard|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_command_id_conflict_visibility_guard|delivery success|真实公网 HTTPS/TLS|4G/SIM|production DB/queue" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_08-09_cloud-command-id-conflict-visibility-guard
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_08-09_cloud-command-id-conflict-visibility-guard
```

## 4. 偏差和范围控制

- 本轮 pre_start/PRD/tech-plan 初始状态写为 planning only；implementation 已由 Robot / Full-Stack worker 完成，本文件记录实际执行结果。
- Product closeout 未修改 Robot/mobile 实现文件。
- 本轮没有新增真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、真实手机/browser、WAVE ROVER/UART/HIL 或真实送达。

## 5. 剩余风险

- Objective 5 仍约 68%，因为本轮只是 Docker/local command/status/ack conflict software proof，不是真实 external proof。
- Objective 1 仍约 81%，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；仍缺真实 2D LiDAR / ToF 与 WAVE ROVER/HIL 材料。
- Objective 4 仍约 99%，mobile/web 本轮只是 fixture/local software proof，不是真实 phone/browser/device acceptance。
- 本轮不证明 delivery success；`command_id_conflict` 表示机器人拒绝冲突命令。
