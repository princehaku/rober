# Field Evidence Real Material Request Dispatch Tech Done

Run time: 2026-05-21 14:22 CST

## Sprint Status

- sprint_type: epic
- capability: `field_evidence_real_material_request_dispatch`
- evidence boundary: `software_proof_docker_field_evidence_real_material_request_dispatch_gate`
- closeout owner: Product Manager / OKR Owner
- product verdict: accepted as Docker/local `software_proof` request dispatch only

## User Value And Product North Star

This sprint turns the repeated field-material blocker into one executable request for field owners. Instead of asking for vague "rerun proof", the product now names the nine same-`evidence_ref` real materials required before O2/O3/O4 can move from local readiness toward real field acceptance.

The north star remains verified autonomous trash delivery: task record, route runtime, route completion, elevator/human-assist evidence, terminal completion, delivery result, phone/browser observation, and diagnostics summary must reconcile to one safe evidence chain before the product claims real delivery progress.

## OKR Mapping

- Objective 5 remains the lowest at about 68%. This sprint does not provide public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, production app/device, or true phone/browser external proof.
- Objective 1 remains about 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` is still unresolved/material pending; comment `3269642220` remains software-proof reply publication only.
- Objectives 2/3/4 remain about 99%. This sprint creates the real-material request dispatch needed for future field acceptance, but it does not include a real `task_record`, `nav2_fixed_route_runtime_log`, `route_completion_signal`, route/elevator field pass, true phone/browser evidence, dropoff/cancel completion, delivery result, or delivery success.

## KR Breakdown And Core Lever

- KR1: Autonomy provides the PC-only gate that consumes previous acceptance-backfill safe state and emits a same-`evidence_ref` field-owner request checklist.
- KR2: Robot exposes the request through a diagnostics-safe alias without raw artifacts, raw diagnostics, ROS topics, serial/UART/WAVE ROVER details, credentials, paths, checksums, tracebacks, ACK/cursor state, HIL/pass wording, or success/control claims.
- KR3: Full-Stack makes the request visible in `mobile/web` as read-only Chinese phone-safe copy while leaving Start Delivery, Confirm Dropoff, and Cancel disabled.
- KR4: Hardware consultation confirms the request category names are acceptable, while preserving vendor-source boundaries and refusing to treat vendor facts as installed hardware, HIL, route field pass, or delivery proof.

## Autonomy Slice

Owner: Autonomy Algorithm Engineer

### 实际改动

- `pc-tools/evidence/field_evidence_real_material_request_dispatch.py`
  - 新增 `trashbot.field_evidence_real_material_request_dispatch.v1` / `trashbot.field_evidence_real_material_request_dispatch_summary.v1` PC gate。
  - 只读消费 previous acceptance-backfill artifact、summary、Robot safe alias 或 wrapper/nested JSON 的 safe state。
  - 输出九类 same safe `evidence_ref` 真实材料请求：`task_record`、`nav2_fixed_route_runtime_log`、`route_completion_signal`、`elevator_door_floor_evidence`、`human_assistance_note`、`dropoff_cancel_completion`、`delivery_result`、`true_phone_browser_evidence`、`diagnostics_mobile_safe_summary`。
  - 保持 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
  - 对缺 source、bad JSON、unsupported schema/boundary、source not ready、evidence_ref mismatch、unsafe/sensitive copy、raw path、credential、ROS topic、serial/UART/WAVE ROVER detail、checksum、traceback、complete/raw artifact 和 success/control claim fail closed。
- `pc-tools/evidence/test_field_evidence_real_material_request_dispatch.py`
  - 覆盖 ready dispatch、missing/unsupported source、evidence_ref mismatch、unsafe/sensitive input、source not ready 和 CLI behavior。
- `pc-tools/README.md`
  - 增加 gate 用法、schema、九类材料、fail-closed 条件和证据边界。
- `docs/interfaces/evidence_contracts.md`
  - 增加 request dispatch contract，明确 artifact/summary schema、allowed inputs、required materials、blocked claims 和 not-proven 边界。

### 验证结果

- `python3 -m py_compile pc-tools/evidence/field_evidence_real_material_request_dispatch.py`
  - Pass。
- `python3 -m unittest pc-tools/evidence/test_field_evidence_real_material_request_dispatch.py`
  - Pass: `Ran 5 tests in 0.160s OK`。
- CLI help
  - Pass。
- required `rg`
  - Pass。
- scoped `git diff --check`
  - Pass。

### 失败定位与修复

- 首轮 `safe_copy` 先脱敏再扫描白名单，导致 unsafe source 可能被脱敏后误判为 safe；已改为先扫描白名单原文，再脱敏输出，保持 fail-closed。

### 剩余风险

- 这是 PC/Docker local software proof request dispatch，不读取或验证真实 field materials，不证明 route/elevator field pass、Nav2/fixed-route、true phone/browser、dropoff/cancel completion、delivery result、HIL、O5 external proof 或 delivery success。

## Robot Diagnostics Slice

Owner: Robot Platform Engineer

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 新增 `robot_diagnostics_field_evidence_real_material_request_dispatch_summary` safe alias。
  - 消费 `trashbot.field_evidence_real_material_request_dispatch_summary.v1` canonical summary，或包含该 summary 的 compatible wrapper。
  - 保留 `software_proof_docker_field_evidence_real_material_request_dispatch_gate`、`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
  - 只输出 safe `evidence_ref`、九类 required materials、owner mapping、next required evidence、blocked claims 和 safe copy。
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 增加 request-dispatch safe alias/fail-closed 单测，覆盖 path ref、nested wrapper、missing、unsupported boundary、evidence_ref mismatch、unsafe raw diagnostics/artifact、success claim 和 diagnostics payload latest_status scrub。
- `docs/interfaces/ros_runtime_contracts.md`
  - 增加 Robot diagnostics alias contract，明确 allowed fields、九类 required material categories 和 not-proven/control-disabled 边界。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - Pass。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - Pass: `Ran 257 tests in 0.901s OK`。
- required `rg`
  - Pass。
- scoped `git diff --check`
  - Pass。

### 失败定位与修复

- 九类 materials 被既有 helper 截成八类，丢掉 `diagnostics_mobile_safe_summary`；已为该 alias 使用完整九类限制。
- `full_stack` 被 broad `ack` unsafe marker 误杀；已把 ACK key marker 缩窄为 `ack_cursor` / `ack_post` / `ack_state`。

### 剩余风险

- Robot diagnostics 只暴露 metadata-only safe alias，不触发 task_orchestrator、Start、Confirm Dropoff、Cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion、delivery result 或 primary robot actions。

## Full-Stack Slice

Owner: User Touchpoint Full-Stack Engineer

### 实际改动

- `mobile/web/app.js`
  - 新增 `field_evidence_real_material_request_dispatch` first-screen “现场真实材料请求” panel。
  - 优先消费 `robot_diagnostics_field_evidence_real_material_request_dispatch_summary`，再兼容 safe summary / nested summary / status diagnostics summary。
  - 展示 request status、source acceptance-backfill、safe `evidence_ref`、same-evidence-ref status、required materials、field-owner next steps、blocked claims、evidence boundary 和 false flags。
  - 保持 read-only，不 fetch raw diagnostics/artifacts，不触发 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、command replay、request/review/handoff/result submission 或 robot command。
- `mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_request_dispatch.json`
  - 新增 safe Robot diagnostics fixture。
- `mobile/web/test_mobile_web_entrypoint.py`
  - 增加 panel rendering、fallback、not-proven flags、required material 和 action-disabled assertions。
- `docs/product/mobile_user_flow.md`
  - 增加手机端“现场真实材料请求”panel 的消费顺序、展示字段、禁读字段和证据边界。

### 验证结果

- `node --check mobile/web/app.js`
  - Pass。
- `python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_request_dispatch.json`
  - Pass。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`
  - Pass: `Ran 213 tests in 1.622s OK`。
- required `rg`
  - Pass。
- scoped `git diff --check`
  - Pass。

### 失败定位与修复

- Worker evidence 未报告 Full-Stack blocker；fixture、rendering 和 docs 已按 read-only / fail-closed boundary 完成。

### 剩余风险

- 本轮不是真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice 或 true phone/browser acceptance。手机 panel 只让 field owner 看见该补什么材料，不提交材料、不执行控制。

## Hardware Read-Only Consultation

Owner: Hardware Infra Engineer

### 实际结论

- 已读 `docs/vendor/VENDOR_INDEX.md` 和 WAVE ROVER vendor files。
- 可用 request material 名称仅作为材料类别，不写成真实电梯、人工协助、route field pass、2D LiDAR、ToF、WAVE ROVER、UART、HIL 或 delivery success 已验证。
- Vendor facts only:
  - WAVE ROVER UART uses newline-delimited JSON.
  - Raspberry Pi examples include sample `/dev/ttyAMA0` at `115200`.
  - `T=1`、`T=13`、`T=1001` facts exist in vendor material.
  - LiDAR examples are examples, not project-installed proof.
  - ToF is not installed proof.

### 剩余风险

- 没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 或 operator HIL report。

## Product Closeout Validation Required

The Product closeout owner must run and report:

```bash
test -f sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/tech-done.md
test -f sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/side2side_check.md
test -f sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/final.md
rg -n "software_proof_docker_field_evidence_real_material_request_dispatch_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|true_phone_browser_evidence|task_record|nav2_fixed_route_runtime_log|route_completion_signal" sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch OKR.md docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch
```

## Targeted Integration Validation Required

The Product closeout owner must rerun the targeted integration fence:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_real_material_request_dispatch.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest pc-tools/evidence/test_field_evidence_real_material_request_dispatch.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_request_dispatch.json >/tmp/field_evidence_real_material_request_dispatch_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "field_evidence_real_material_request_dispatch|robot_diagnostics_field_evidence_real_material_request_dispatch_summary|software_proof_docker_field_evidence_real_material_request_dispatch_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/field_evidence_real_material_request_dispatch.py pc-tools/evidence/test_field_evidence_real_material_request_dispatch.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_request_dispatch.json mobile/web/test_mobile_web_entrypoint.py docs/interfaces/evidence_contracts.md docs/interfaces/ros_runtime_contracts.md docs/product/mobile_user_flow.md
git diff --check -- pc-tools/evidence/field_evidence_real_material_request_dispatch.py pc-tools/evidence/test_field_evidence_real_material_request_dispatch.py pc-tools/README.md docs/interfaces/evidence_contracts.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_request_dispatch.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Remaining Product Risks

- No Objective percentage should increase from this sprint.
- This sprint is not real field rerun, not real `task_record`, not real Nav2/fixed-route runtime, not route/elevator field pass, not true phone/browser proof, not dropoff/cancel completion, not delivery result, not delivery success, not HIL, not WAVE ROVER/UART proof, not O5 external proof, and not PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution.
- The next acceptance step requires field owner to return the nine requested real materials under the same safe `evidence_ref`; only then should Product consider intake/review of O2/O3/O4 field evidence.
