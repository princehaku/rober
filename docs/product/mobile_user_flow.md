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

## Mobile Web Entrypoint

The standalone phone entrypoint now lives in `mobile/web/`:

- `index.html`, `styles.css`, and `app.js` implement a dependency-free phone-first shell.
- `manifest.webmanifest`, `service-worker.js`, `offline.html`, and SVG icons provide the minimal PWA shell.
- `mobile/fixtures/mobile_web_status.fixture.json` is marked as a static smoke fixture and is not live robot state.

This entrypoint consumes the existing phone-safe contract only. It reads `/api/status`, `/api/diagnostics`, `phone_readiness`, `command_safety`, and `phone_offline_resume_readiness`; it can render optional `phone_task_flow_readiness`, `phone_support_bundle`, and `voice_prompt_readiness` when they are present. It does not add robot state names or reinterpret ROS2 delivery semantics.

Start Delivery, Confirm Dropoff, and Cancel are disabled by default. The browser enables them only when `command_safety.actions.<action>.enabled=true` and the legacy permission fields also allow the same action. Blocked, offline, pending ACK, and manual-takeover states stay disabled. Diagnostics and Support Handoff remain visible while primary actions are blocked, because support collection must not require making motion-related controls available.

Start Delivery now has an explicit mobile task-start confirmation gate before the primary action button. The page must show the phone-safe target trash station or destination, require the user to check "trash loaded" manually, and show the current blocking reason. The destination can come from `phone_task_flow_readiness.destination_summary`, a `destination_confirmed` step, `phone_readiness.destination`, or `status.destination`; if none of those safe fields exist, Start remains disabled. This confirmation is a user action only, not automatic load detection.

`POST /api/collect` from `mobile/web/` is no longer body-less. The request body uses `schema=trashbot.mobile_task_start_confirmation.v1`, `schema_version=1`, `source=mobile_web`, a phone-safe `destination`, `target` with the same phone-safe destination for `/api/collect` compatibility, `trash_loaded_confirmed=true`, client timestamp/reference, `evidence_boundary=software_proof_docker_mobile_task_start_confirmation_gate`, and ACK semantics stating accepted/processing only. The payload must not include raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, credentials, local paths, complete artifacts, or checksums.

The Start button is enabled only when all four gates pass: `command_safety.actions.start.enabled=true`, legacy `can_collect=true`, a safe destination is present, and the user has checked the load confirmation. Missing `command_safety`, missing destination, unchecked load confirmation, offline state, blocked state, pending ACK, or manual takeover all fail closed. ACK copy must remain visible as command accepted/processing evidence only and must not be described as delivery success.

The mobile PWA now makes that rule visible as a first-screen three-step primary journey summary:

1. Target trash station.
2. Manual trash-loaded confirmation.
3. Start safety gate.

This is `software_proof_docker_mobile_primary_journey_gate`. It proves only that the Docker/local `mobile/web/` shell and targeted unit test can render the primary journey, keep Start fail closed, and submit the existing `/api/collect` compatible `target` field inside a phone-safe confirmation envelope. It is not a real iPhone/Android test, not a production app, not a real PWA install prompt, not Nav2/fixed-route execution, not WAVE ROVER/HIL, and not delivery success.

The target trash station in this summary must come only from existing phone-safe fields: `phone_task_flow_readiness.destination_summary`, a confirmed `destination_confirmed` step, `phone_readiness.destination`, `status.destination`, or the same sanitized destination reused as `/api/collect.target` for compatibility. The page must not expose raw ROS topics, `/cmd_vel`, serial device names, baudrate values, WAVE ROVER parameters, credentials, DB/queue URLs, local paths, tracebacks, checksums, or complete artifacts.

The trash-loaded step is a user confirmation only. The UI must not claim automatic load detection, automatic weighing, camera detection, or any sensor-derived proof of loaded trash unless a future backend contract explicitly provides that capability and the evidence boundary is updated.

The start safety gate must consume existing `phone_task_flow_readiness`, `command_safety`, cloud readiness, device/browser readiness, `operation_log` / `phone_operation_log`, and `mobile_action_receipt` / `phone_action_feedback`. Missing fields, blocked status, offline/unreachable state, pending ACK, manual takeover or human-help state, missing destination, and unchecked load confirmation all fail closed. ACK, HTTP accepted, and receipts remain accepted/processing evidence only; they do not prove delivery success, dropoff success, cancel completion, HIL, production readiness, or true robot motion.

`mobile_primary_journey_gate` and `mobile_primary_journey_summary` may appear in `/api/status` or `/api/diagnostics` as phone-safe support metadata. They are not robot commands, remote ACKs, cursors, delivery results, production readiness grants, or robot compatibility proof by themselves.

The mobile PWA now includes a first-screen “恢复决策” panel immediately after the three-step primary journey. It prioritizes `mobile_recovery_decision_gate` and `mobile_recovery_decision_summary`, including compatible copies nested under `phone_readiness` or `/api/diagnostics`. When those fields are missing, the page derives only a blocked-by-design summary from existing phone-safe fields: offline/resume readiness, command safety, operation log, action feedback/receipt, support handoff, and primary journey readiness. It does not invent robot state.

The recovery decision schema is `trashbot.mobile_recovery_decision_gate.v1`, and the Docker/local evidence boundary is `software_proof_docker_mobile_recovery_decision_gate`. The panel shows recovery state, recommended next action, blocking reason, support entry, ACK semantics, evidence boundary, and `not_proven` summary. It must give Chinese-first recovery advice for pending ACK, offline or stale status, manual takeover / human help, local submit failed, missing primary journey readiness, and missing support handoff.

The recovery decision panel is read-only. It must not call Start Delivery, Confirm Dropoff, Cancel, ACK routes, cursor updates, or robot command routes. It must not describe ACK, HTTP accepted, or receipt metadata as delivery success, dropoff success, cancel completed, production readiness, HIL, or true robot completion. Its local/static proof does not prove real iPhone/Android behavior, a production app, a real PWA install prompt, real HTTPS/TLS, real 4G/SIM, OSS/CDN live traffic, production DB/queue, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, real cancel completion, real dropoff completion, or real delivery.

The mobile PWA service worker caches only the static shell. It bypasses `/api/*`, `/robots/*`, command routes, ACK routes, diagnostics, and all non-GET requests with `no-store`. The offline shell does not cache, queue, or replay control requests; it shows recovery copy and keeps primary actions disabled.

The cloud-relay runtime can now host this same `mobile/web/` shell at `/` and `/index.html`, with assets at `/app.js`, `/styles.css`, `/manifest.webmanifest`, `/service-worker.js`, `/offline.html`, `/icon-192.svg`, and `/icon-512.svg`. API/probe/control routes keep priority: `/robots/*`, `/healthz`, `/readyz`, `/preflightz`, command routes, ACK routes, and unknown `/api/*` paths must not be served by static fallback. Missing static assets and path traversal attempts return phone-safe JSON 404 without local absolute paths.

The same cloud-relay handler provides phone-safe, same-origin `GET /api/status` and `GET /api/diagnostics` for the hosted shell. These two static-phone APIs do not require bearer auth, select `TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID` or `trashbot-001`, and wrap the relay store's latest `/robots/{robot_id}/status` into a safe summary when present. If the relay has no status, the phone receives `state=status_missing` and `overall_status=blocked` rather than a browser-level 404. The adapter always keeps Start Delivery, Confirm Dropoff, and Cancel fail closed with `can_collect=false`, `can_confirm_dropoff=false`, `can_cancel=false`, `phone_readiness.can_continue=false`, and `command_safety.actions.*.enabled=false`.

The evidence boundary is `software_proof_docker_cloud_hosted_mobile_web_gate`; it proves only Docker/local hosted shell routing plus phone-safe status/diagnostics adapter behavior. It does not prove real public cloud, HTTPS/TLS, 4G/SIM, real phone device/browser behavior, production app, PWA install prompt, OSS/CDN live traffic, production DB/queue, Nav2/fixed-route, WAVE ROVER, HIL, or delivery success. The adapter must not expose token, Authorization, DB/queue URL, local path, ROS topic, serial, WAVE ROVER, `/cmd_vel`, traceback, complete artifact, or any command/status/ACK robot contract change.

The mobile PWA now includes a read-only operation log panel. It first consumes `operation_log` or `phone_operation_log` when the status payload provides them. If neither field exists, it derives a minimal recent-event list only from existing phone-safe fields: `phone_readiness`, `command_safety`, `phone_task_flow_readiness`, `phone_offline_resume_readiness`, `phone_support_bundle`, and `voice_prompt_readiness`. The panel shows Chinese-first recent events, recovery hints, ACK wording, and support handoff copy, but it does not open Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, or delivery-success paths.

The operation log evidence boundary is `software_proof_docker_mobile_operation_log_gate`. This proves the local/static mobile page can render phone-safe recent events, recovery hints, and support handoff entry from fixture/status payloads while keeping Start/Confirm/Cancel fail-closed. It does not prove real phone device/browser behavior, a production app, a real PWA install prompt, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or real delivery.

Operation log content must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB or queue URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums, full artifacts, or any wording that turns ACK into delivery success.

The mobile PWA now includes an action feedback panel for Start Delivery, Confirm Dropoff, and Cancel. It shows the most recent user action, submission state, failure or blocking reason, recovery hint, `client_reference`, ACK semantics, and the evidence boundary. The panel consumes `mobile_action_receipt` or `phone_action_feedback` when the status payload provides them; if a local submit request fails, the page shows local `failed` / `blocked` copy. Local failure copy is deliberately narrow: it only says the phone/API submit layer failed or did not receive accepted/processing evidence. It does not say that the robot moved, arrived, dropped off, stopped, canceled, or completed the task.

Confirm Dropoff and Cancel now use a generic mobile action confirmation body:

```json
{
  "schema": "trashbot.mobile_action_confirmation.v1",
  "schema_version": 1,
  "source": "mobile_web",
  "action": "confirm_dropoff",
  "user_confirmed": true,
  "client_reference": "mobile_web_confirm_dropoff_...",
  "client_timestamp": "ISO-8601 timestamp",
  "safe_phone_copy": "确认投放 已由用户二次确认提交，等待 accepted/processing 证据。",
  "ack_semantics": "accepted_processing_only_not_delivery_success",
  "evidence_boundary": "software_proof_docker_mobile_action_feedback_gate"
}
```

The same schema is used for `action=cancel`. It is a phone-safe confirmation envelope only. It must not include raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, token values, Authorization headers, OSS AK/SK, DB or queue URLs, local filesystem paths, complete artifacts, or checksums.

The action feedback evidence boundary is `software_proof_docker_mobile_action_feedback_gate`. This proves the local/static mobile page can render phone-safe action receipts, local submit failures, recovery hints, client references, and ACK wording from fixture/status payloads. It does not prove real phone device/browser behavior, a production app, a real PWA install prompt, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, real dropoff, real cancel completion, or real delivery.

ACK, HTTP accepted, or receipt copy must remain accepted/processing evidence only. The page must not describe those events as delivery success, dropoff success, cancel completed, Nav2/fixed-route success, WAVE ROVER movement, real cloud/4G readiness, HIL pass, or true task completion.

The mobile PWA now includes a first-screen “云中转状态” panel for cloud/preflight/DB/queue readiness. It consumes only phone-safe metadata from `phone_cloud_readiness_summary`, `mobile_cloud_readiness_summary`, `cloud_readiness_summary`, or `phone_readiness.cloud_readiness`. The panel shows overall status, preflight status, DB/queue status, `production_ready`, ACK semantics, evidence boundary, and recovery guidance in Chinese-first copy.

The cloud readiness summary schema is `trashbot.phone_cloud_readiness_summary.v1`. The local/static evidence boundary is `software_proof_docker_mobile_cloud_readiness_summary_gate`. The summary may reference upstream Docker/local proof such as `software_proof_docker_cloud_db_queue_config_gate`, but this is only a source boundary for sanitized readiness copy. It does not prove real phone device/browser behavior, a production app, real HTTPS/TLS, a public cloud entrypoint, real 4G/SIM, OSS/CDN live traffic, production DB/queue, multi-instance consistency, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or real delivery.

When the cloud readiness summary is missing, `overall_status=blocked`, `production_ready=false`, or the backend has not explicitly set `primary_actions_enabled=true` / `safe_to_control=true`, the page keeps Start Delivery, Confirm Dropoff, and Cancel disabled. Diagnostics and Support Handoff remain visible so support can inspect or copy sanitized information without enabling motion-related controls. This gate is intentionally conservative: a present preflight or DB/queue config summary is not a user-control grant by itself.

The cloud readiness panel and fixture must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB URLs, queue URLs, credential-bearing URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums, complete artifacts, or wording that turns ACK into delivery success. ACK copy must remain accepted/processing evidence only and must not be described as real cloud readiness, production queue success, task success, dropoff success, cancel completion, HIL, or true delivery.

The mobile PWA now includes a first-screen “手机验收准备” panel for real mobile-device/browser acceptance readiness. It consumes only phone-safe metadata from `mobile_device_acceptance_readiness`, `phone_device_acceptance_readiness`, `mobile_browser_acceptance_readiness`, or the same fields nested under `phone_readiness` or `/api/diagnostics`. The panel shows viewport/touch readiness, PWA install prompt/offline readiness, diagnostics/cloud gate readiness, `production_app_ready`, recovery guidance, ACK semantics, and evidence boundary.

The device acceptance readiness schema is `trashbot.mobile_device_acceptance_readiness.v1`. The local/static evidence boundary is `software_proof_docker_mobile_device_acceptance_readiness_gate`. This proves the local/static mobile page can render a phone-safe blocked-by-design readiness summary and keep primary actions disabled when real phone/browser or production app evidence is missing. It does not prove real iPhone/Android behavior, a production app, a real PWA install prompt, real cloud/4G, OSS/CDN live traffic, production DB/queue, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or real delivery.

When the device acceptance readiness summary is missing, `overall_status=blocked`, `safe_to_control` is not true, or the backend has not simultaneously set `primary_actions_enabled=true` and `production_app_ready=true`, the page keeps Start Delivery, Confirm Dropoff, and Cancel disabled. Diagnostics and Support Handoff remain visible because support and recovery must not require enabling motion-related controls.

The device acceptance panel and fixture must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB URLs, queue URLs, credential-bearing URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums, complete artifacts, or wording that turns ACK into delivery success. ACK copy must remain accepted/processing evidence only and must not be described as real phone acceptance, production app readiness, delivery success, dropoff success, cancel completion, HIL, or true delivery.

The mobile PWA now includes a first-screen “浏览器验收包” panel and copy button for phone/support metadata. It prioritizes `mobile_browser_acceptance_bundle`, `phone_browser_acceptance_bundle`, and `mobile_acceptance_evidence_bundle`, including the same fields nested under `phone_readiness` or `/api/diagnostics`. When those fields are missing, the page derives a blocked-by-design summary only from existing phone-safe readiness, cloud, offline, diagnostics, and command-safety fields.

The browser acceptance bundle schema is `trashbot.mobile_browser_acceptance_bundle.v1`, `schema_version=1`, and the Docker/local evidence boundary is `software_proof_docker_mobile_browser_acceptance_bundle_gate`. The bundle contains only `overall_status`, `production_app_ready`, `safe_to_control`, `viewport`, `touch_target`, `pwa_install_prompt`, `offline_shell`, `diagnostics`, `cloud_gate`, `action_gate`, `ack_semantics`, `client_timestamp`, `safe_phone_copy`, `recovery_hint`, `evidence_boundary`, and `not_proven`. It is a copyable phone/support metadata package, not a robot command, not a remote ACK, and not a production readiness grant.

When the browser acceptance bundle is missing, `overall_status=blocked`, `safe_to_control=false`, `production_app_ready=false`, or `not_proven` still includes real device/browser, production app, or real PWA install prompt, Start Delivery, Confirm Dropoff, and Cancel must fail closed. Diagnostics and Support Handoff stay available so users can reproduce the blocked state and send a sanitized summary to support. The page must state that ACK is accepted/processing evidence only and not delivery success, dropoff success, cancel completion, real cloud readiness, HIL, or true delivery.

The browser acceptance bundle and copied support text must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB URLs, queue URLs, credential-bearing URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums, complete artifacts, or wording that turns ACK into delivery success. Local/Docker fixture proof does not prove real iPhone/Android behavior, a production app, a real PWA install prompt, real cloud/4G, OSS/CDN live traffic, production DB/queue, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or real delivery.

Evidence boundary: `software_proof_docker_mobile_web_entrypoint_gate`. This proves the static entrypoint and smoke checks exist; it does not prove production app readiness, real iPhone/Android browser behavior, real service-worker install prompt, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or delivery success.

The local page also shows live robot location when localization is publishing. `operator_gateway` subscribes to `/amcl_pose` by default and includes `robot_pose` plus recent `robot_path` points in `GET /api/status`; without AMCL data the controls still work, but the map panel waits for pose updates.

`GET /api/diagnostics` is the minimum support package for phone UI and remote support. It reports software version, map and route version labels, latest status, last task summary, machine-readable failure fields, log references, the operator status file, the vision sample manifest reference, and phone-safe O6 summaries such as `oss_cdn_manifest`, `network_recovery_drill`, `credential_rotation`, `provisioning_audit`, `production_store_queue`, `queue_ordering_drill`, `transaction_isolation`, and `production_recovery`. It does not claim that those files exist; it gives support tools stable references to inspect.

The local browser page is phone-first and uses the API fields directly: task state, `phone_copy`, `speaker_prompt`, action permissions, robot pose/path, and diagnostics. The page is still intentionally dependency-free HTML served by `operator_gateway`; it is a usable local control surface, not a production account system.

The first screen now includes a phone readiness gate derived from `/api/status.phone_readiness`. This gate answers three user questions before raw diagnostics: can the phone continue, why not, and what should happen next. It aggregates local delivery state, action permissions, local/mock remote readiness, optional cloud preflight, optional backup/restore drill summaries, and O6 artifact summaries including `oss_cdn_manifest`, `network_recovery`, `credential_rotation`, `provisioning_audit`, `production_store_queue`, `queue_ordering_drill`, `transaction_isolation`, and `production_recovery`. It is a local/Docker software proof boundary only and must not be presented as production phone app, real phone browser/device acceptance, real cloud, real 4G, real OSS/CDN, production DB/queue, production queue ordering, production transaction isolation, production backup/disaster recovery, Nav2/fixed-route delivery, WAVE ROVER motion, or HIL proof.

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

The first screen also exposes `voice_prompt_readiness` at top-level `/api/status`, nested under `phone_readiness.voice_prompt_readiness`, and in `GET /api/diagnostics`. The schema is `trashbot.voice_prompt_readiness.v1`, and the evidence boundary is `software_proof_docker_phone_voice_prompt_readiness_gate`. It shows the current prompt contract, trigger state, human-help requirement, playback readiness, safe phone copy, ACK semantics, and explicit `not_proven` boundaries. This is a prompt readiness gate only: `playback_ready=false` in the local/Docker proof, ACK is accepted/processing evidence only, and the object does not prove real speaker playback, TTS, microphone wake word, real phone device, production app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or delivery success.

The first screen and offline shell now also expose `phone_offline_resume_readiness` at top-level `/api/status`, nested under `phone_readiness.phone_offline_resume_readiness`, and in `GET /api/diagnostics`. The schema is `trashbot.phone_offline_resume_readiness.v1`, and the evidence boundary is `software_proof_docker_phone_offline_resume_gate`. This gate combines offline shell copy, reconnect/recovery hints, stale status, pending ACK, command safety, support handoff, voice prompt boundary, and ACK semantics into one phone-safe local/Docker contract. It does not cache, forge, or send Start/Confirm/Cancel control requests while offline. Start Delivery, Confirm Dropoff, and Cancel remain disabled in the offline shell; the live page still uses `command_safety` as the final button-level blocker. Diagnostics and Support Handoff remain accessible when primary actions are blocked, so users can recover or hand off a sanitized summary without making motion claims.

`phone_offline_resume_readiness` fields:

- `schema`: `trashbot.phone_offline_resume_readiness.v1`.
- `schema_version`: integer version, currently `1`.
- `evidence_boundary`: `software_proof_docker_phone_offline_resume_gate`.
- `connection_state`: `offline`, `status_stale`, `pending_ack`, `blocked`, `manual_takeover`, `recovering`, or `online`.
- `can_resume`: true only when connection state is online and command safety allows at least one primary action.
- `primary_actions_enabled`: whether Start/Confirm/Cancel currently have any enabled action after command safety.
- `support_entry_enabled`: whether Diagnostics or Support Handoff can still be opened.
- `next_action`: recovery action such as `wait_reconnect`, `wait_for_robot_status`, `wait_for_command_ack`, `retry_cloud`, `manual_takeover`, or `continue_local_flow`.
- `safe_phone_copy`: Chinese-first user copy for the first screen or offline/resume panel.
- `recovery_hint`: user-facing recovery step.
- `ack_semantics`: ACK remains accepted/processing evidence only and is not delivery success.
- `support_handoff`: sanitized support-entry summary.
- `voice_prompt`: prompt-readiness boundary summary; local/Docker proof does not prove real playback.
- `command_safety`: compact summary of the final browser button gate.
- `offline_shell`: confirms primary actions stay disabled and no control request cache is used.
- `not_proven`: explicit non-claims including real phone device/browser, production app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, and delivery success.

The offline/resume summary must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB/queue URLs, raw ROS topic names, `/cmd_vel`, serial device names, baudrate values, local filesystem paths, checksums, or complete artifacts.

`voice_prompt_readiness` must be Chinese-first when a Chinese prompt exists. For elevator assisted delivery, `trigger_state=requesting_floor_help` must surface:

```text
你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,
```

The voice prompt summary is phone-safe. It must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB/queue URLs, raw ROS topic names, `/cmd_vel`, serial device names, baudrate values, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums, or complete artifacts.

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
- `voice_prompt_readiness`: phone-safe voice prompt readiness package with `schema=trashbot.voice_prompt_readiness.v1` and evidence boundary `software_proof_docker_phone_voice_prompt_readiness_gate`. `/api/status.voice_prompt_readiness`, `/api/status.phone_readiness.voice_prompt_readiness`, and `/api/diagnostics.voice_prompt_readiness` use the same summary and include `current_prompt`, `prompt_language`, `trigger_state`, `trigger_reason`, `requires_human_help`, `playback_ready=false`, `safe_phone_copy`, `ack_semantics`, `support_refs`, and `not_proven`.
- `phone_offline_resume_readiness`: phone-safe offline/resume package with `schema=trashbot.phone_offline_resume_readiness.v1` and evidence boundary `software_proof_docker_phone_offline_resume_gate`. `/api/status.phone_offline_resume_readiness`, `/api/status.phone_readiness.phone_offline_resume_readiness`, and `/api/diagnostics.phone_offline_resume_readiness` use the same summary and include connection state, resume allowance, primary action gate, support-entry gate, next action, recovery hint, ACK semantics, offline shell boundary, and `not_proven`.
- `mobile_device_acceptance_readiness`: phone-safe real-device/browser acceptance package with `schema=trashbot.mobile_device_acceptance_readiness.v1` and evidence boundary `software_proof_docker_mobile_device_acceptance_readiness_gate`. `/api/status.mobile_device_acceptance_readiness`, compatible `phone_device_acceptance_readiness` / `mobile_browser_acceptance_readiness` aliases, nested `phone_readiness.*_acceptance_readiness`, and `/api/diagnostics.*_acceptance_readiness` may use the same summary. It includes viewport/touch readiness, PWA install prompt/offline readiness, diagnostics/cloud gate readiness, `production_app_ready`, `primary_actions_enabled`, optional `safe_to_control`, recovery hint, ACK semantics, and explicit `not_proven` boundaries.
- `mobile_browser_acceptance_bundle`: phone-safe browser acceptance package with `schema=trashbot.mobile_browser_acceptance_bundle.v1` and evidence boundary `software_proof_docker_mobile_browser_acceptance_bundle_gate`. `/api/status.mobile_browser_acceptance_bundle`, compatible `phone_browser_acceptance_bundle` / `mobile_acceptance_evidence_bundle` aliases, nested `phone_readiness.*_acceptance_bundle`, and `/api/diagnostics.*_acceptance_bundle` may use the same summary. It includes viewport, touch target, PWA install prompt, offline shell, diagnostics, cloud gate, action gate, client timestamp, safe copy, recovery hint, ACK semantics, and `not_proven`; it must stay blocked-by-design until real mobile browser and production app evidence exists.
- `mobile_recovery_decision_gate`: phone-safe recovery decision package with `schema=trashbot.mobile_recovery_decision_gate.v1` and evidence boundary `software_proof_docker_mobile_recovery_decision_gate`. `/api/status.mobile_recovery_decision_gate`, compatible `mobile_recovery_decision_summary`, nested `phone_readiness.mobile_recovery_decision_*`, and `/api/diagnostics.mobile_recovery_decision_*` may use the same summary. It includes recovery state, next action, blocking reason, support entry, safe copy, recovery hint, ACK semantics, and `not_proven`; it is a read-only support and user-decision summary, not a robot command, ACK, cursor, delivery success, dropoff success, cancel completion, production readiness, or HIL proof.
- `remote_readiness`: current local/mock remote readiness object.
- `cloud_preflight` / `backup_restore`: optional phone-safe gate summaries; missing artifacts remain `not_run` or `unknown`.
- `oss_cdn_manifest`: phone-safe diagnostic object reference summary. It uses `schema=trashbot.oss_cdn_manifest`, `schema_version=1`, `evidence_boundary=software_proof_docker_phone_manifest_consumption`, `state=ready|missing|invalid|stale`, `object_count`, `cdn_url_rule`, `safe_summary`, `retry_hint`, `updated_at`, `staleness`, and `not_proven`. It must not expose the full artifact, object keys, checksums, local paths, credentials, ROS topics, or hardware details.
- `production_store_queue`: phone-safe production DB/queue gate summary. It uses `schema=trashbot.production_store_queue_gate`, `schema_version=1`, `evidence_boundary=software_proof_docker_production_store_queue_phone_consumption`, `state=ready|missing|invalid|stale`, `store_contract_status`, `queue_contract_status`, `ordering_status`, `consistency_status`, `migration_status`, `production_ready=false`, `overall_status=blocked`, `safe_summary`, `retry_hint`, `generated_at`, `staleness`, and `not_proven`. It must not expose the full artifact, checksum, local paths, DB URLs, queue URLs, credentials, ROS topics, or hardware details.
- `queue_ordering_drill`: phone-safe Docker/local queue ordering drill summary. It uses `schema=trashbot.queue_ordering_drill`, `schema_version=1`, `evidence_boundary=software_proof_docker_queue_ordering_phone_consumption`, `state=ready|missing|invalid|stale|failed`, `ordering_invariant`, `concurrency_invariant`, `cursor_invariant`, `ack_invariant`, `adjacent_command_ids`, `observed_order`, `production_ready=false`, `overall_status`, `safe_summary`, `retry_hint`, `updated_at`, `staleness`, and `not_proven`. It must not expose the full artifact, checksum, local paths, DB URLs, queue URLs, credentials, ROS topics, hardware details, or imply true production queue ordering.
- `transaction_isolation`: phone-safe Docker/local transaction isolation drill summary. It uses `schema=trashbot.transaction_isolation_drill`, `schema_version=1`, `evidence_boundary=software_proof_docker_transaction_isolation_phone_consumption`, `state=ready|missing|invalid|stale|failed`, `scenario`, `command_a_id`, `command_b_id`, `command_a_ack_state`, `command_b_ack_state`, `terminal_ack_ids`, `cursor_before`, `cursor_after_interleaving`, `cursor_invariant`, `ack_invariant`, `delivery_success=false`, `production_ready=false`, `overall_status`, `safe_summary`, `retry_hint`, `updated_at`, `staleness`, and `not_proven`. It must not expose the full artifact, checksum, local paths, DB URLs, queue URLs, credentials, ROS topics, hardware details, or imply true production transaction isolation.
- `production_recovery`: phone-safe Docker/local production backup/disaster recovery gate summary. It uses `schema=trashbot.production_recovery_gate`, `schema_version=1`, `evidence_boundary=software_proof_docker_production_recovery_phone_consumption`, `state=ready|missing|invalid|stale|failed|blocked`, `local_backup_restore_status`, `recovery_drill_status`, `production_backup_policy_status`, `disaster_recovery_status`, `state_backend_status`, `db_queue_status`, `multi_instance_status`, `retention_status`, `restore_objective_status`, `ack_semantics`, `production_ready=false`, `overall_status=blocked`, `safe_summary`, `retry_hint`, `updated_at`, `staleness`, and `not_proven`. It must not expose the full artifact, checksum, local paths, DB URLs, queue URLs, backup paths, credentials, ROS topics, hardware details, or imply true production backup/disaster recovery.
- `not_proven`: explicit list of product or hardware capabilities this local gate does not prove.

`oss_cdn_manifest.state=ready` only means the phone/API can consume a sanitized diagnostic reference summary generated from a local manifest artifact. It does not prove real OSS upload, STS issuance, CDN origin fetch, real cloud, real 4G/SIM, Nav2/fixed-route delivery, WAVE ROVER motion, delivery success, or HIL. `missing`, `invalid`, and `stale` must keep the first screen out of a green ready state and show ordinary user copy such as "诊断对象引用缺失。", "诊断对象引用损坏。", or "诊断对象引用已过期。" plus a retry hint to refresh or regenerate references.

ACK remains command processing evidence only. A remote ACK may make `remote_readiness.degradation_state=ok`, but the phone must keep reading delivery status for `completed`, `failed`, `needs_human_help`, or elevator-assist states. The UI text must explain that ACK means command accepted or processing evidence only; it does not prove delivery success, Nav2/fixed-route success, WAVE ROVER movement, real cloud/4G, or HIL.

## Local Mobile Web Browser Acceptance Gate

The current browser acceptance gate targets the standalone `mobile/web/` PWA, not the older onboard fallback operator gateway. It starts a lightweight static HTTP server, serves `mobile/web/`, and uses `mobile/fixtures/mobile_web_status.fixture.json` as the phone-safe response for both `/api/status` and `/api/diagnostics`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence
```

The gate opens the served PWA in a real local Chromium-family browser through Chrome DevTools Protocol and checks `390x844` plus `768x900` viewports. It verifies primary Start/Confirm/Cancel buttons remain disabled, Diagnostics and Support Handoff remain available, the browser acceptance bundle is visible and copyable, ACK copy remains accepted/processing evidence only, interactive hit areas are at least 44 CSS px, key first-screen elements avoid horizontal overflow and unreasonable overlap, and visible text does not leak token, Authorization, OSS AK/SK, DB/queue URL, ROS topic, `/cmd_vel`, serial, baudrate, WAVE ROVER, local paths, traceback, checksum, or complete artifact wording.

Successful runs write `mobile_web_browser_390x844.json/png`, `mobile_web_browser_768x900.json/png`, and `mobile_web_browser_acceptance_summary.json` into the sprint `evidence/` directory. This evidence boundary is `software_proof_docker_mobile_web_browser_proof_gate`. It proves a real local Chromium-family browser rendered the dependency-free PWA against a phone-safe fixture; it does not prove a real iPhone/Android device, production app, real PWA install prompt, real cloud/4G, OSS/CDN live traffic, production DB/queue, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or delivery success.

## Cloud-Hosted PWA Installability Gate

`pc-tools/evidence/cloud_hosted_pwa_installability_gate.py` verifies the same `mobile/web/` PWA through a Docker/local `cloud-relay` hosted URL. It starts the relay, requests hosted static routes, and writes `cloud_hosted_pwa_installability_summary.json` plus 390x844 and 768x900 browser evidence into the sprint evidence directory. The evidence boundary is `software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`.

The manifest check covers `name`, `short_name`, `start_url`, `scope`, `display=standalone`, theme/background color, icons, `evidence_boundary=software_proof_docker_mobile_web_entrypoint_gate`, and `installability_evidence_boundary=software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`. The hosted response header must still show `software_proof_docker_cloud_hosted_mobile_web_gate`, because the relay is the serving surface while installability is the browser/PWA acceptance gate layered on top.

The service worker check proves static shell and dynamic control traffic stay separated: `/api/*`, `/robots/*`, commands, ACK, diagnostics, and every non-GET request bypass cache with `no-store`; the script must not use offline queue/replay storage for control requests. The offline shell keeps Start Delivery, Confirm Dropoff, and Cancel disabled and only explains reconnect/recovery. The browser check keeps 390x844 and 768x900 viewports, verifies Start/Confirm/Cancel fail closed, Diagnostics and Support remain available, ACK copy is not delivery success, the browser evidence bundle is visible/copyable, key touch targets are at least 44 CSS px, and the layout has no horizontal overflow.

This is Docker/local cloud-hosted browser/PWA software proof only. It is not a real iPhone/Android device test, not a production app, not a real PWA install prompt, not real HTTPS/TLS public ingress, not real 4G/SIM, not OSS/CDN live traffic, not production DB/queue proof, not Nav2/fixed-route delivery, not WAVE ROVER/HIL, and not real delivery success.

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
