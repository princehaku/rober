# Tech Plan - PR5 mandatory sensor material owner-response review handoff

- sprint_type: epic
- sprint: `2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff`
- target capability: `pr5_mandatory_sensor_material_owner_response_review_handoff`
- proof boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中完成度最低的 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5 的外部云证明；本 sprint 针对 PR #5 mandatory sensor material unresolved thread，主映射 Objective 1，并支持 Objective 4 只读用户触点。
3. 不针对 Objective 5 的理由：最近 08-09、09-10、10-11 三轮 O5 command lifecycle/export/support/intake 都是 Docker/local software proof，均 `no OKR percentage lift`，且当前仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result。继续叠 O5 local metadata wrapper 会重复消费同一外部证据 blocker。本轮选择 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending` 作为更可执行的证据链推进。
4. Objective 1 约 81%，但 PR #5 unresolved thread 是当前明确 reviewer evidence；本轮只进入 `pr5_mandatory_sensor_material_owner_response_review_handoff`，不宣称硬件完成度提升。

## 总体方案

本轮从上一轮 `pr5_mandatory_sensor_material_owner_response_review_decision` 进入
`pr5_mandatory_sensor_material_owner_response_review_handoff`。三路并行实现互不重叠：

- Hardware 负责 PC handoff gate。
- Robot 负责 diagnostics safe alias。
- Full-Stack 负责 read-only mobile panel。

Product 只做验收和 closeout，不提前更新 `OKR.md` 或 `docs/process/okr_progress_log.md`。所有输出都必须保留：

- `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`
- `PRRT_kwDOSWB9286CJ3tX`
- `hardware_material_pending`
- `docs/vendor/VENDOR_INDEX.md`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`

## 并行 Engineer 任务

### Task A - Hardware PC handoff gate

- owner: `robot-hardware-engineer`
- priority: P0
- responsibility: 创建 PC handoff gate，把 owner-response review-decision safe artifact/summary 转成 review-handoff safe artifact/summary。
- allowed files:
  - `pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_handoff.py`
  - `pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_review_handoff.py`
  - `pc-tools/README.md`
  - `docs/product/production_hardware_boundary.md`
  - `docs/interfaces/pr5_mandatory_sensor_material_owner_response_review_handoff.md`
  - current sprint `tech-done.md`
- forbidden:
  - raw hardware config changes
  - launch defaults
  - serial/UART device assumptions
  - `OKR.md` before Product closeout
- required behavior:
  - Input capability must be `pr5_mandatory_sensor_material_owner_response_review_decision`.
  - Output capability must be `pr5_mandatory_sensor_material_owner_response_review_handoff`.
  - Summary must include PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`.
  - Summary must cite `docs/vendor/VENDOR_INDEX.md` as source entrypoint and explicitly state source attribution is not real hardware proof.
  - Summary must include owner/support/reviewer handoff, next required evidence, safe `evidence_ref`, safe copy, and false-state flags.
- validation commands:
  - `python3 -m py_compile pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_handoff.py`
  - `python3 -m unittest pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_review_handoff.py`
  - `rg -n "pr5_mandatory_sensor_material_owner_response_review_handoff|software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|docs/vendor/VENDOR_INDEX.md|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools docs sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff`
  - scoped `git diff --check` for touched Hardware files only

### Task B - Robot diagnostics safe alias

- owner: `robot-software-engineer`
- priority: P0
- responsibility: 创建 Robot diagnostics safe alias，并嵌入 status/diagnostics phone-safe surface。
- allowed files:
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
  - `onboard/src/ros2_trashbot_behavior/test/`
  - `docs/interfaces/ros_runtime_contracts.md`
  - `docs/product/remote_4g_mvp.md`
  - current sprint `tech-done.md`
- forbidden:
  - `/cmd_vel` exposure
  - control endpoints
  - ACK/cursor mutation
  - raw artifact fetch
  - GitHub mutation
  - `OKR.md` before Product closeout
- required behavior:
  - Publish `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary`.
  - Prefer backend-provided sanitized summary; never infer real hardware proof from truthy fields.
  - Preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
  - Preserve `not_proven`, `source=software_proof`, and `hardware_material_pending`.
  - Redact raw local paths, credentials, checksums, raw diagnostics, serial/UART details, complete artifacts, and success/control copy.
- validation commands:
  - targeted py_compile for touched Robot files
  - targeted Robot unittest for diagnostics alias and status/diagnostics exposure
  - `rg -n "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary|pr5_mandatory_sensor_material_owner_response_review_handoff|software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" onboard docs sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff`
  - scoped `git diff --check` for touched Robot files only

### Task C - Full-Stack read-only mobile panel

- owner: `full-stack-software-engineer`
- priority: P0
- responsibility: 创建 `mobile/web` read-only panel，展示 PR5 mandatory sensor material owner-response review handoff。
- allowed files:
  - `mobile/web/index.html`
  - `mobile/web/styles.css`
  - `mobile/web/app.js`
  - `mobile/web/fixtures/`
  - `mobile/test/`
  - `docs/product/mobile_user_flow.md`
  - current sprint `tech-done.md`
- forbidden:
  - primary action enablement
  - upload/material fetch endpoint
  - GitHub mutation
  - ACK/cursor routes
  - replay/resubmit controls
  - raw diagnostics display
  - `OKR.md` before Product closeout
- required behavior:
  - Panel title should make the PR5 material handoff state obvious to support users.
  - The panel must consume `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary` first, then safe fallback fields only.
  - Show `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, owner/support/reviewer handoff, next required evidence, source boundary, evidence boundary, and safe copy.
  - Show false-state flags and keep Start Delivery / Confirm Dropoff / Cancel disabled when this is the only new material.
  - Missing/unsafe summary must render blocked/not_proven copy.
- validation commands:
  - `node --check mobile/web/app.js`
  - targeted mobile unittest for fixture rendering and unsafe summary fail-closed behavior
  - fixture `python3 -m json.tool` check where JSON fixtures are added
  - `rg -n "pr5_mandatory_sensor_material_owner_response_review_handoff|robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary|software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile docs sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff`
  - scoped `git diff --check` for touched Full-Stack files only

## Product closeout plan

After the three Engineer tasks land and pass validation, `product-okr-owner` must:

1. Review `tech-done.md` evidence from Hardware, Robot, and Full-Stack.
2. Create `side2side_check.md` comparing required PR #5 thread state, false-state flags, docs sync, and UI/Robot/PC evidence.
3. Create `final.md` with outcome, validation summary, no OKR percentage lift, and explicit non-goals.
4. Only then update `OKR.md` and `docs/process/okr_progress_log.md`.

Product closeout expected result unless real evidence changes:

- Objective 5 remains about 68%。
- Objective 1 remains about 81%。
- `no OKR percentage lift`。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`。
- 本轮不是 HIL、不是 WAVE ROVER/UART proof、不是 real LiDAR/ToF proof、不是 true phone/browser proof、不是 O5 external proof、不是 delivery success。

## 验收命令

本规划文档验收命令：

```bash
test -f sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/pre_start.md && test -f sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/prd.md && test -f sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/tech-plan.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|pr5_mandatory_sensor_material_owner_response_review_handoff|software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|docs/vendor/VENDOR_INDEX.md" sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff
```

```bash
git diff --check -- sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/pre_start.md sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/prd.md sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/tech-plan.md
```

## 风险和阻塞

- 当前无真实硬件，只有 Docker/local；不得宣称 real LiDAR/ToF proof、WAVE ROVER/UART/HIL 或 route/elevator field pass。
- PR #5 thread 仍 unresolved；不得把 comment `3269642220` 或 software-proof reply publication 写成 thread resolution。
- PR #7 review-thread/comments live query若超时，不得用缺失工具结果推导“无评审问题”。
- O5 external proof 仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result。
- 本轮最多形成可执行 handoff，不形成 OKR percentage lift。
