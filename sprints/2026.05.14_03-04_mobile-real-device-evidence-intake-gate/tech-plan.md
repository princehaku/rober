# Sprint 2026.05.14_03-04 Mobile Real Device Evidence Intake Gate - Tech Plan

## Sprint Type

sprint_type: epic

## 目标

实现 `software_proof_docker_mobile_real_device_evidence_intake_gate` 的计划边界：Full-stack 在 `mobile/web` 首屏提供真实设备验收材料导入/生成入口，Robot 侧提供 metadata-only compatibility fence。Product 本轮已创建 `pre_start.md`、`prd.md`、`tech-plan.md`；后续实现由 Full-stack 与 Robot 并行执行。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中完成度最低的是 Objective 5，约 68%。Objective 4 约 79%。
2. 本 sprint 不直接针对 Objective 5 completion，主目标是 Objective 4 的真实手机设备 / production app / PWA install prompt 验收材料 intake。
3. 不针对 Objective 5 的理由：`OKR.md` 第 6 节要求只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 等外部材料时才继续推进 O5；本轮没有这些材料，继续本地 O5 metadata depth 会重复消费同一 blocked 状态。最新 `02-03` final 也建议在没有 O5 外部材料时转向真实 iPhone/Android 或 production app/PWA prompt 验收材料。

## 架构与接口边界

### Schema

计划新增 phone/support metadata schema：

```json
{
  "schema": "trashbot.mobile_real_device_evidence_intake.v1",
  "schema_version": 1,
  "source": "mobile_web",
  "overall_status": "blocked",
  "device": {
    "platform": "unknown",
    "model_summary": "not_provided",
    "os_summary": "not_provided"
  },
  "browser": {
    "family": "unknown",
    "version_summary": "not_provided",
    "viewport_css": {"width": 0, "height": 0},
    "device_pixel_ratio": 0,
    "orientation": "unknown",
    "touch_target_summary": "not_proven"
  },
  "pwa": {
    "display_mode": "unknown",
    "install_prompt_status": "not_observed",
    "install_prompt_user_choice": "not_provided",
    "manifest_status": "unknown",
    "service_worker_status": "unknown",
    "offline_shell_status": "unknown"
  },
  "production_app": {
    "ready": false,
    "entry_url_summary": "not_provided",
    "release_summary": "not_provided"
  },
  "evidence": {
    "screenshot_summary": "not_provided",
    "url_summary": "not_provided",
    "observer_note": "not_provided",
    "redaction_status": "passed"
  },
  "safe_to_control": false,
  "ack_semantics": "accepted_processing_only_not_delivery_success",
  "evidence_boundary": "software_proof_docker_mobile_real_device_evidence_intake_gate",
  "not_proven": [
    "真实手机设备",
    "真实 iPhone/Android device behavior",
    "production app",
    "真实 PWA install prompt/user choice",
    "real delivery"
  ]
}
```

Compatible field names:

- `mobile_real_device_evidence_intake`
- `mobile_real_device_evidence_intake_summary`
- `mobile_real_device_evidence_package`
- Nested under `phone_readiness` or `/api/diagnostics` when backend provides it.

### Redaction Rules

Allowed summary fields:

- device/browser/viewport/display-mode/PWA install prompt/user choice/production app readiness summaries.
- screenshot summary and URL summary only, not full artifact content.
- short client reference, client timestamp, observer note, redaction status, `not_proven`, `safe_phone_copy`, recovery hint.

Forbidden fields:

- token, Authorization, OSS AK/SK, root password, DB/queue URL.
- ROS topic, `/cmd_vel`, serial, baudrate, WAVE ROVER parameters.
- local filesystem paths, traceback, checksum, complete artifact, raw robot response, credential-bearing URL.

### Control Boundary

The intake package is support/acceptance metadata only. It must not be treated as:

- `trashbot.remote.v1` command/status/ACK envelope.
- ROS2 action, service, topic, cursor, persisted terminal ACK id, delivery result, production readiness result, HIL result, or hardware proof.
- Start Delivery / Confirm Dropoff / Cancel enablement source by itself.

## Team 分工

### Task A - Full-stack

Owner: User Touchpoint Full-Stack Engineer（Full-stack）

Allowed files for implementation phase:

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `mobile/README.md`
- `sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/tech-done.md`

Implementation notes:

- Add first-screen “真实设备验收材料” panel after existing device/handoff/install prompt/browser proof surfaces.
- Generate blocked-by-design package when no imported real-device material exists.
- Provide import/generate/copy path for phone-safe package.
- Keep Start Delivery、Confirm Dropoff、Cancel fail closed unless existing gates independently allow them; this gate must not grant control.
- Technical comments in changed code must be Chinese and keep the repo's comment-ratio rule.

Acceptance commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "software_proof_docker_mobile_real_device_evidence_intake_gate|mobile_real_device_evidence_intake|真实手机设备|production app|PWA install prompt|not_proven|redaction" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md mobile/README.md sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/tech-done.md
```

### Task B - Robot

Owner: Robot Platform Engineer（Robot）

Allowed files for implementation phase:

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/tech-done.md`

Implementation notes:

- Add compatibility tests proving `mobile_real_device_evidence_intake` / summary / package are metadata-only.
- Verify metadata-only response does not trigger collect, confirm_dropoff, cancel, ACK POST, cursor advance, cursor persistence, `last_terminal_ack_id`, delivery success, dropoff success, cancel completed, production readiness, HIL, or hardware proof.
- Preserve valid command behavior when metadata appears beside a valid command envelope: only the command envelope controls execution.
- Update interface docs with the field contract and non-claim boundary.

Acceptance commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "mobile_real_device_evidence_intake|software_proof_docker_mobile_real_device_evidence_intake_gate|metadata-only|delivery success|PWA install prompt|production app|真实手机设备" docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/tech-done.md
```

### Task C - Product Closeout

Owner: Product Manager / OKR Owner

Allowed files for closeout phase:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/tech-done.md`
- `sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/side2side_check.md`
- `sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/final.md`

Acceptance commands:

```bash
test -f sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/tech-done.md && test -f sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/side2side_check.md && test -f sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/final.md
rg -n "software_proof_docker_mobile_real_device_evidence_intake_gate|Objective 4|Objective 5|真实手机设备|production app|PWA install prompt|not_proven|ACK" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate
```

## 并行执行要求

- Task A Full-stack 与 Task B Robot 文件范围互不重叠，必须并行派发。
- 两者都可写 `tech-done.md`，但必须分区追加，不覆盖对方结果。
- Product Closeout 等 A/B 返回后执行，不提前写 final 或 OKR progress。

## 本轮启动文档验收命令

```bash
test -f sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/pre_start.md && test -f sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/prd.md && test -f sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/tech-plan.md
rg -n "sprint_type: epic|software_proof_docker_mobile_real_device_evidence_intake_gate|OKR 最低优先级核对|Objective 5|Objective 4|真实手机设备|production app|PWA install prompt|Full-stack|Robot" sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate
git diff --check -- sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate
```

## 剩余风险

- 本轮启动计划本身不产生 software proof；只有 Full-stack 和 Robot 实现、测试、文档同步完成后，才能收口为 `software_proof_docker_mobile_real_device_evidence_intake_gate`。
- 真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 和真实 delivery 仍需后续独立证据链。
- 如果后续真实设备材料不能被导入或只能靠未脱敏截图交接，本 sprint 不能算产品验收闭环。
