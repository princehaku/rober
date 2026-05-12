# Mobile User Flow

## Minimum User Journey

1. User connects phone to the robot network or local control page.
2. User opens the local operator gateway.
3. User selects or confirms the trash station.
4. User places trash on the robot.
5. User taps start after confirming the load.
6. Robot announces or displays that it is preparing to depart.
7. Robot travels to the station.
8. Robot announces arrival and asks for removal or confirms dropoff.
9. User taps confirm after removing or disposing of the load.
10. Robot returns, waits, or reports that human help is required.

## Status States

- Waiting for trash.
- Loaded and ready.
- Delivering.
- Elevator assisted delivery states when enabled for a dry-run or controlled H2 route:
  - `approaching_elevator`
  - `waiting_elevator_open`
  - `entering_elevator`
  - `requesting_floor_help`
  - `waiting_target_floor`
  - `exiting_elevator`
  - `resume_delivery`
- Arrived at station.
- Returning.
- Completed.
- Needs human help.

## Exception Handling

The phone UI should show plain-language messages:

- "Route is not ready."
- "Robot cannot find the trash station."
- "Navigation failed."
- "电梯未开门，需要人工协助。"
- "未确认目标楼层，请人工确认。"
- "目标楼层证据不可靠，请人工确认。"
- "需要人工接管电梯段任务。"
- "Please remove trash manually."
- "Robot stopped for safety."

Users should not need SSH, ROS2 commands, serial tools, or direct hardware debugging for the normal flow.

## Minimum Local API

The first operator gateway is intentionally small: an API-first local HTTP service plus a minimal browser page at `/`. It is enough for a phone browser on the robot network, but it is not a polished native app, does not include account/login flows, and does not replace hardware bringup checks.

- `GET /api/status`
- `GET /api/diagnostics`
- `POST /api/collect`
- `POST /api/dropoff/confirm`
- `POST /api/cancel`

This is enough for a phone page or local browser control surface to complete a dry-run task and drive the manual dropoff confirmation service.

The local page also shows live robot location when localization is publishing. `operator_gateway` subscribes to `/amcl_pose` by default and includes `robot_pose` plus recent `robot_path` points in `GET /api/status`; without AMCL data the controls still work, but the map panel waits for pose updates.

`GET /api/diagnostics` is the minimum support package for phone UI and remote support. It reports software version, map and route version labels, latest status, last task summary, machine-readable failure fields, log references, the operator status file, the vision sample manifest reference, and phone-safe O6 summaries such as `oss_cdn_manifest`, `network_recovery_drill`, `credential_rotation`, `provisioning_audit`, `production_store_queue`, and `queue_ordering_drill`. It does not claim that those files exist; it gives support tools stable references to inspect.

The local browser page is phone-first and uses the API fields directly: task state, `phone_copy`, `speaker_prompt`, action permissions, robot pose/path, and diagnostics. The page is still intentionally dependency-free HTML served by `operator_gateway`; it is a usable local control surface, not a production account system.

The first screen now includes a phone readiness gate derived from `/api/status.phone_readiness`. This gate answers three user questions before raw diagnostics: can the phone continue, why not, and what should happen next. It aggregates local delivery state, action permissions, local/mock remote readiness, optional cloud preflight, optional backup/restore drill summaries, and O6 artifact summaries including `oss_cdn_manifest`, `network_recovery`, `credential_rotation`, `provisioning_audit`, `production_store_queue`, and `queue_ordering_drill`. It is a local/Docker software proof boundary only and must not be presented as production phone app, real phone browser/device acceptance, real cloud, real 4G, real OSS/CDN, production DB/queue, production queue ordering, Nav2/fixed-route delivery, WAVE ROVER motion, or HIL proof.

The current fallback phone page also exposes `phone_task_flow_readiness` as a top-level `/api/status` field and as `phone_readiness.phone_task_flow_readiness`. The schema is `trashbot.phone_task_flow_readiness.v1`, and the evidence boundary is `software_proof_docker_phone_task_flow_readiness_gate`. It organizes the first screen and diagnostics around the user task flow:

- `connection_ready`: whether the phone can use the local control entry.
- `destination_confirmed`: the user-visible trash station or a reminder to confirm it before departure.
- `trash_loaded`: explicit user confirmation that trash has been placed on the robot; this is not automatic load detection.
- `start_delivery`: the one-tap departure gate, still controlled by action permissions and command safety.
- `status_explained`: plain-language task state such as waiting, delivering, arrived, returning, completed, failed, or needs human help.
- `help_or_diagnostics`: diagnostics and manual takeover entry. Diagnostics can remain accessible while Start/Confirm/Cancel are blocked.

`GET /api/diagnostics` now includes the same `phone_task_flow_readiness` summary so support can reproduce which first-screen step was blocked. This diagnostics copy is a support summary only; it does not make the task ready, does not trigger robot actions, and does not prove delivery success.

The same object now includes `command_safety`, a stricter browser button gate for Start Delivery, Confirm Dropoff, Cancel, and Diagnostics. `phone_readiness.can_continue` may still indicate that a user can continue observing the local fallback page, but Start/Confirm/Cancel must remain disabled when the command gate sees stale status, a pending command ACK, auth failure, cloud unreachable, malformed remote response, missing/invalid/stale diagnostic references, or a manual takeover state. Diagnostics remains accessible so support data can be collected, but the page must explain the blocking reason and must not make Start/Confirm appear green just because Diagnostics can open.

The first screen now also exposes a support handoff entry backed by `phone_support_bundle`. This is a sanitized copy/paste package for a user, family member, after-sales support, or engineering support when the task is failed, blocked, waiting for ACK, or requires human takeover. It is not a raw diagnostics dump: it reuses the same status, `phone_readiness`, `command_safety`, and diagnostics summaries, then filters tokens, Authorization headers, OSS AK/SK, root passwords, DB/queue URLs, raw ROS topic names, `/cmd_vel`, serial device names, baudrate values, WAVE ROVER parameters, local paths, tracebacks, checksums, and complete artifacts. Support/Handoff and Diagnostics remain accessible when Start/Confirm/Cancel are blocked by command safety.

`phone_readiness` fields:

- `schema`: `trashbot.phone_readiness.v1`.
- `schema_version`: integer version, currently `1`.
- `evidence_boundary`: `software_proof_docker_phone_task_flow_readiness_gate`.
- `primary_state`: phone-first state such as `ready`, `local_ready_remote_status_waiting`, `waiting_for_robot_status`, `waiting_for_command_ack`, `login_required`, `remote_unreachable`, `remote_response_invalid`, `manual_takeover_required`, or `monitoring`.
- `can_continue`: whether the current phone journey has a safe next step.
- `next_action`: machine-readable next action such as `continue_local_flow`, `continue_local_or_wait_remote_status`, `wait_for_robot_status`, `wait_for_command_ack`, `check_auth`, `retry_cloud`, `contact_support`, `manual_takeover`, or `watch_progress`.
- `safe_phone_copy`: user-facing summary for the first screen.
- `recovery_hint`: user-facing next-step copy.
- `support_level`: support classification such as `phone_ready`, `local_fallback`, `remote_blocked`, `remote_waiting_ack`, or `support_required`.
- `local_delivery`: current local state plus `phone_copy` and `speaker_prompt`.
- `phone_task_flow_readiness`: task-step metadata with schema `trashbot.phone_task_flow_readiness.v1`, step list, destination summary, load-confirmation requirement, start gate, status explanation, diagnostics/help entry, ACK semantics, blocking reasons, and `not_proven`.
- `action_permissions`: copies `can_collect`, `can_confirm_dropoff`, and `can_cancel`.
- `command_safety`: browser command gate with `schema=trashbot.command_safety.v1`, evidence boundary `software_proof_docker_phone_command_safety_browser_gate`, `global_block_reason`, `ack_semantics`, `safe_phone_copy`, and per-action entries for `start`, `confirm_dropoff`, `cancel`, and `diagnostics`. Each primary action combines the old `can_*` permission with remote readiness and manifest safety. `diagnostics.enabled` may stay true while its copy explains the block.
- `phone_support_bundle`: phone-safe handoff package with `schema=trashbot.phone_support_bundle.v1` and evidence boundary `software_proof_docker_phone_support_bundle_gate`. `/api/status.phone_support_bundle`, `/api/status.phone_readiness.phone_support_bundle`, and `/api/diagnostics.phone_support_bundle` use the same builder and include `bundle_id`, `generated_at`, `support_level`, `status_summary`, `failure_summary`, `next_steps`, `ack_semantics`, `support_refs`, `safe_copy`, and `not_proven`. `safe_copy` is Chinese-first and must state that ACK means accepted/processing evidence only, not delivery success.
- `remote_readiness`: current local/mock remote readiness object.
- `cloud_preflight` / `backup_restore`: optional phone-safe gate summaries; missing artifacts remain `not_run` or `unknown`.
- `oss_cdn_manifest`: phone-safe diagnostic object reference summary. It uses `schema=trashbot.oss_cdn_manifest`, `schema_version=1`, `evidence_boundary=software_proof_docker_phone_manifest_consumption`, `state=ready|missing|invalid|stale`, `object_count`, `cdn_url_rule`, `safe_summary`, `retry_hint`, `updated_at`, `staleness`, and `not_proven`. It must not expose the full artifact, object keys, checksums, local paths, credentials, ROS topics, or hardware details.
- `production_store_queue`: phone-safe production DB/queue gate summary. It uses `schema=trashbot.production_store_queue_gate`, `schema_version=1`, `evidence_boundary=software_proof_docker_production_store_queue_phone_consumption`, `state=ready|missing|invalid|stale`, `store_contract_status`, `queue_contract_status`, `ordering_status`, `consistency_status`, `migration_status`, `production_ready=false`, `overall_status=blocked`, `safe_summary`, `retry_hint`, `generated_at`, `staleness`, and `not_proven`. It must not expose the full artifact, checksum, local paths, DB URLs, queue URLs, credentials, ROS topics, or hardware details.
- `queue_ordering_drill`: phone-safe Docker/local queue ordering drill summary. It uses `schema=trashbot.queue_ordering_drill`, `schema_version=1`, `evidence_boundary=software_proof_docker_queue_ordering_phone_consumption`, `state=ready|missing|invalid|stale|failed`, `ordering_invariant`, `concurrency_invariant`, `cursor_invariant`, `ack_invariant`, `adjacent_command_ids`, `observed_order`, `production_ready=false`, `overall_status`, `safe_summary`, `retry_hint`, `updated_at`, `staleness`, and `not_proven`. It must not expose the full artifact, checksum, local paths, DB URLs, queue URLs, credentials, ROS topics, hardware details, or imply true production queue ordering.
- `not_proven`: explicit list of product or hardware capabilities this local gate does not prove.

`oss_cdn_manifest.state=ready` only means the phone/API can consume a sanitized diagnostic reference summary generated from a local manifest artifact. It does not prove real OSS upload, STS issuance, CDN origin fetch, real cloud, real 4G/SIM, Nav2/fixed-route delivery, WAVE ROVER motion, delivery success, or HIL. `missing`, `invalid`, and `stale` must keep the first screen out of a green ready state and show ordinary user copy such as "诊断对象引用缺失。", "诊断对象引用损坏。", or "诊断对象引用已过期。" plus a retry hint to refresh or regenerate references.

ACK remains command processing evidence only. A remote ACK may make `remote_readiness.degradation_state=ok`, but the phone must keep reading delivery status for `completed`, `failed`, `needs_human_help`, or elevator-assist states. The UI text must explain that ACK means command accepted or processing evidence only; it does not prove delivery success, Nav2/fixed-route success, WAVE ROVER movement, real cloud/4G, or HIL.

## Local Phone Browser Acceptance Gate

The local operator page now has a Docker/local browser acceptance gate for the fallback phone surface:

```bash
python3 scripts/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence
```

The gate starts a lightweight local operator fixture, opens the served HTML in a real Chromium-family browser, and checks `390x844` plus `768x900` viewports. It verifies button hit areas are at least 44 CSS px, Start/Confirm/Cancel stay disabled in a blocked command-safety state, Diagnostics remains accessible, ACK copy is visible, and key first-screen text does not overlap.

This evidence boundary is `software_proof_docker_phone_browser_acceptance_gate`. It does not prove a production phone app, real iPhone/Android device behavior, real cloud/4G, OSS/CDN traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or delivery success. The local page keeps raw JSON status hidden by default so ordinary phone users see readiness, command safety, ACK semantics, recovery hints, and Diagnostics entry copy instead of ROS or hardware internals.

## Local PWA Installability Gate

The local operator fallback page now exposes a minimal PWA shell for Docker/local software proof:

- `GET /manifest.webmanifest` returns `name`, `short_name`, `start_url`, `scope`, `display`, `theme_color`, `background_color`, and icon entries. `start_url` and `scope` stay on the operator shell and do not point to `/api/*`.
- The HTML head includes viewport, theme color, description, Apple mobile web app title/capable/status-bar meta, and a manifest link.
- `GET /service-worker.js` registers a static shell cache for `/`, `/index.html`, `/offline.html`, and `/manifest.webmanifest` only.
- The service worker treats `/api/*`, `/robots/*`, command routes, ACK routes, diagnostics, and every non-GET request as dynamic control traffic and fetches them with `cache: 'no-store'`.
- `GET /offline.html` is a phone-safe offline shell. It says the phone is disconnected and reconnect is required; Start Delivery, Confirm Dropoff, and Cancel remain disabled.

The evidence boundary is `software_proof_docker_phone_pwa_installability_gate`. It does not prove a production app, real iPhone/Android installation prompt, real phone device Safari/Chrome behavior, real cloud, real 4G/SIM, production account system, OSS/CDN traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or delivery success.

For H2 elevator assisted delivery dry-runs, `GET /api/status` and `GET /api/diagnostics` may include an `elevator_assist` object. Older clients can ignore it. New clients should treat it as the machine-readable source for elevator UI:

- `enabled`: boolean; false means normal single-floor delivery UI.
- `mode`: expected to be `dry_run` until controlled real-world validation exists.
- `state` / `phase`: current elevator sub-state or failure reason.
- `requires_human_help`: true when the phone should ask for operator or bystander help.
- `reason`: machine-readable explanation such as `door_timeout`, `target_floor_unconfirmed`, or `unsafe_to_exit`.
- `target_floor`: target floor label when known.
- `phone_copy`: user-facing copy for the phone.
- `speaker_prompt`: prompt contract for a future speaker/TTS layer; the local gateway does not play audio.
- `evidence`: dry-run evidence such as `door_open`, `door_closed_or_unknown`, `inside_elevator`, `target_floor_confirmed`, `target_floor_unconfirmed`, `safe_to_exit`, or `unsafe_to_exit`.
- `events`: ordered elevator sub-state events when a task record provides them.

When `phase=requesting_floor_help`, `speaker_prompt` must be:

```text
你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,
```

## Phone Status And Speaker Prompt Contract

`operator_gateway` emits these strings in every status-style JSON payload as `phone_copy` and `speaker_prompt`, so phone UI and speaker/voice layers share the same state contract.

| State | Phone copy | Speaker prompt |
| --- | --- | --- |
| `waiting_for_trash` | Waiting for trash. Place trash on the robot, then start delivery. | Please place trash on the robot. |
| `loaded_and_ready` | Trash is loaded. Ready to deliver. | Trash loaded. Preparing to depart. |
| `delivering` | Delivering to the selected trash station. | Delivering trash now. |
| `waiting_elevator_open` | 已到电梯厅，等待电梯开门。 | 等待电梯开门。 |
| `requesting_floor_help` | 已进入电梯，正在请求帮忙按楼层。 | 你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯, |
| `waiting_target_floor` | 正在等待目标楼层，请保持通道安全。 | 正在等待目标楼层。 |
| `target_floor_unconfirmed` | 未确认目标楼层，请人工确认。 | 未确认目标楼层，需要人工协助。 |
| `unsafe_to_exit` | 目标楼层出口不安全，需要人工接管。 | 需要人工协助。 |
| `resume_delivery` | 已驶出电梯，继续送往垃圾站。 | 已驶出电梯，继续送垃圾。 |
| `arrived_at_station` | Arrived. Remove or dispose of the load, then confirm dropoff. | Arrived at the trash station. Please remove the trash. |
| `returning` | Dropoff confirmed. Returning or waiting for the next task. | Dropoff confirmed. Returning now. |
| `completed` | Task completed. | Task completed. |
| `canceling` | Cancel request sent. Waiting for the robot to stop. | Cancel request sent. |
| `canceled` | Task canceled. The robot is stopped or returning to standby. | Task canceled. |
| `failed` | Task failed. Check diagnostics or request help. | Task failed. Please check the phone. |
| `needs_human_help` | Human help is required. Follow the shown instruction. | Human help is required. |

## 4G Remote MVP

The first 4G path is a robot-side outbound polling bridge, not a production account system. Start it only when needed with `remote_bridge:=true` and a mock or future `remote_cloud_base_url`; the default launch value is off.

The mock-cloud command set mirrors the local user journey:

- `collect` starts the behavior collection action.
- `confirm_dropoff` submits the manual dropoff confirmation.
- `cancel` requests cancellation of the active collection.

The robot posts status and command acknowledgements back to the cloud endpoint so the same flow can be tested offline before choosing a real cloud provider.

The local mock cloud may be started with a configured persistence path such as `mock_cloud_state_path`. When this path is empty, the mock keeps the old in-memory behavior. When it is set, the mock writes only command queue, ACK, status and summary counters to a local JSON proof file. The proof file must not contain bearer tokens, serial device names, ROS topic names, baudrate values, WAVE ROVER parameters, or hardware configuration fields.

Local/mock cloud endpoints can be protected with a bearer token. When the gate is enabled, the phone or robot bridge must send `Authorization: Bearer <token>`; missing or wrong tokens return a phone-safe `401` response with `auth_state=auth_failed`. The response never echoes the token, the Authorization header, raw cloud URL credentials, serial settings, hardware parameters, ROS topic names, or velocity-control details.

Phone clients should treat the remote status payload as the user-facing source of truth for local/mock remote-control readiness. `remote_ready=true` only means the current local/mock control-plane conditions allow the phone flow to continue. It does not prove real cloud hosting, HTTPS, SIM/4G connectivity, HIL, WAVE ROVER movement, Nav2/fixed-route success, or trash delivery completion. `GET /robots/{robot_id}/status`, `POST /robots/{robot_id}/status`, `POST /robots/{robot_id}/commands`, and `POST /robots/{robot_id}/commands/{command_id}/ack` may include `remote_readiness` with these fields:

| Field | Meaning for phone UI |
| --- | --- |
| `remote_ready` | true when the local/mock cloud gate, robot status freshness, and pending command state allow the phone to continue. This is not real cloud/4G/HIL proof. |
| `cloud_reachable` | true when this local mock control-plane process handled the request; it does not prove real HTTPS, SIM, or production cloud reachability. |
| `last_command_ack` | latest command id that has an ACK state, or empty when no command has been acknowledged. |
| `status_stale` | true when the robot has not posted status or the status age exceeds the mock freshness window. |
| `retry_hint` | phone-safe next action: `ok`, `wait_for_robot_status`, `wait_for_command_ack`, `check_auth`, `retry_cloud`, or `contact_support`. |
| `auth_state` | mock authentication state: `mock_not_required`, `required`, `authorized`, or `auth_failed`. |
| `degradation_state` | phone-safe readiness class: `ok`, `status_stale`, `command_pending`, `auth_failed`, `cloud_unreachable`, or `malformed_response`. |
| `safe_phone_copy` | ordinary user-facing copy for the phone UI. It must not contain raw JSON, ROS names, hardware details, credentials, or cloud URL secrets. |
| `pending_command_count` | count of queued commands without ACK. |
| `queue_persisted` | true when a local proof file is configured and queue/status/ACK can survive process restart. |

These fields explain remote control readiness only. ACK means the robot bridge accepted, ignored, or failed a command submission; it does not mean trash delivery, Nav2/fixed-route motion, WAVE ROVER movement, or HIL validation succeeded.

Recommended phone handling:

- `ok`: keep the main flow enabled.
- `status_stale`: show "正在等待小车上报最新状态，请稍后再试。"
- `command_pending`: keep destructive actions disabled until an ACK appears.
- `auth_failed`: ask the user to sign in again or check the access code.
- `cloud_unreachable`: ask the user to retry later or switch to local fallback when available.
- `malformed_response`: ask the user to contact support and attach diagnostics.

## 4G Remote Product Path

For a 4G robot, the formal phone path is cloud-mediated rather than phone-to-robot WiFi:

```text
phone web/app -> cloud API -> robot remote_bridge over outbound 4G HTTP polling -> ROS2 behavior
```

The local operator gateway remains a development and fallback entrypoint. The 4G MVP contract is documented in `docs/product/remote_4g_mvp.md`.
