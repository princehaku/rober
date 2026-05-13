# ROS Contracts

## Hardware: `esp32_bridge`

Vendor sources:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

### Parameters

| Name | Type | Default | Contract |
| --- | --- | --- | --- |
| `serial_port` | string | `/dev/ttyUSB0` | Canonical UART device parameter. Confirm the Orange Pi device on hardware. |
| `serial_baudrate` | int | `115200` | Canonical UART baudrate parameter. Vendor examples use `115200`. |
| `port` | string | empty | Deprecated alias for `serial_port`. |
| `baudrate` | int | `0` | Deprecated alias for `serial_baudrate`; ignored when `0`. |
| `command_mode` | string | `speed` | `speed` maps `/cmd_vel` to vendor `T=1`; `ros` maps to vendor `T=13`. |
| `track_width_m` | double | `0.172` | Differential-drive width used by `speed` mode. Must be positive. Current default is project tuning and requires HIL confirmation before production use. |
| `max_wheel_speed_mps` | double | `1.3` | Normalization limit for project-side `T=1` left/right values. Must be positive. Vendor WAVE ROVER materials describe `-0.5` to `0.5` as the user-facing speed range, so the current scaling/clamp remains HIL-pending. |
| `feedback_interval_ms` | int | `100` | Sent to vendor `T=142`. Must be non-negative. |
| `odom_publish_hz` | double | `20.0` | ROS-side `/odom` publish rate. Must be positive. |

### Consumed Topics

| Topic | Type | Contract |
| --- | --- | --- |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | In `speed` mode, `linear.x` and `angular.z` are converted to normalized `T=1` `L`/`R`; positive `angular.z` makes left lower and right higher. In `ros` mode, the bridge sends `T=13` `X`/`Z`. |

### Produced Topics

| Topic | Type | Contract |
| --- | --- | --- |
| `/odom` | `nav_msgs/msg/Odometry` | Command-integrated odometry from last accepted `/cmd_vel`; not encoder-validated or fused localization. |
| `/imu/data` | `sensor_msgs/msg/Imu` | Yaw-only orientation derived from vendor `T=1001` field `y`. |
| `/battery` | `sensor_msgs/msg/BatteryState` | Voltage-only battery state from vendor `T=1001` field `v`. |

### Services

| Service | Type | Contract |
| --- | --- | --- |
| `/trashbot/stop` | `std_srvs/srv/Trigger` | Sends vendor `T=1` stop with `L=0`, `R=0`. |
| `/trashbot/reset_odom` | `std_srvs/srv/Trigger` | Resets ROS-side command-integrated odometry only; no ESP32 reset command is sent. |
| `/trashbot/beep` | `std_srvs/srv/Trigger` | Currently returns unsupported because the WAVE ROVER base JSON contract does not define a beep command. |

### UART Startup Contract

On startup the bridge sends:

1. `{"T":143,"cmd":0}` to disable UART echo.
2. `{"T":142,"cmd":feedback_interval_ms}` to set feedback interval.
3. `{"T":131,"cmd":1}` to enable streamed base feedback.

The ESP32 feedback frame used by this contract is vendor `T=1001` with at least `L`, `R`, `r`, `p`, `y`, and `v`.

## Behavior: `collect_trash`

### Action Server

| Name | Type | Contract |
| --- | --- | --- |
| `/trashbot/collect_trash` | `ros2_trashbot_interfaces/action/TrashCollection` | Default product entry point is `task_orchestrator`; the legacy standalone server is installed as `legacy_trash_collection_server` only for compatibility and aborts goals with `legacy_server_quarantined` instead of reporting demo success. |

### Feedback Fields

| Field | Contract |
| --- | --- |
| `status` | Compatibility numeric status: `0` idle/failure, `1` navigating, `3` delivering/dropoff, `4` done. |
| `percent_complete` | Compatibility progress percentage from `0` to `100`. |
| `current_step` | Compatibility readable step name. |
| `state` | Delivery state machine state, such as `loaded`, `delivering`, `dropoff`, `returning`, `idle`, or `error`. |
| `event` | Latest state machine event, including `invalid_transition` for rejected public transitions. |
| `message` | Human-readable progress or failure detail. |
| `elapsed_sec` | Elapsed action time in seconds. |

### Delivery Parameters

| Parameter | Values | Contract |
| --- | --- | --- |
| `delivery_mode` | `dry_run`, `waypoint`, `fixed_route` | `dry_run` succeeds without Nav2. `waypoint` resolves `delivery_target`/goal frame in `waypoint_file` and uses Nav2. `fixed_route` only reads `fixed_route_status_file`; it does not control UART or hardware directly. |
| `navigation_timeout_sec` | float seconds | Maximum duration for a waypoint or fixed-route attempt. |
| `navigation_retry_limit` | integer | Additional retry attempts after the first navigation attempt. |
| `dropoff_mode` | `dry_run`, `manual_confirm` | `dry_run` confirms immediately. `manual_confirm` waits through `dropoff_timeout_sec` unless canceled. |
| `dropoff_timeout_sec` | float seconds | Manual dropoff confirmation window. |
| `return_target` | waypoint name or empty | Optional return waypoint. Empty means no return navigation. |

### Dropoff Confirmation Service

| Name | Type | Contract |
| --- | --- | --- |
| `/trashbot/confirm_dropoff` | `std_srvs/srv/SetBool` | Valid only while a `manual_confirm` dropoff is pending. `request.data=true` confirms the user has removed or disposed of the load. `request.data=false` rejects the dropoff and the delivery action fails. `response.success=false` means no dropoff confirmation was pending. |

### Operator Gateway

The optional `operator_gateway` node exposes a local HTTP API for phone or browser control without requiring SSH or ROS2 CLI access.

| Endpoint | Method | Contract |
| --- | --- | --- |
| `/api/status` | GET | Returns `state`, `message`, `updated_at`, and the latest task metadata such as `task_record_path`, `error_message`, progress, or target when available. |
| `/api/diagnostics` | GET | Returns the minimum remote-support diagnostic package: software version, map/route versions, latest status, last task summary, terminal failure fields, route proof summary + mapped route proof state, log references, vision sample manifest reference, hardware proof summary, and operator status file path. |
| `/api/vision/review-queue` | GET | Returns review queue samples with `review_status` and `last_decision` summary, plus progress aggregates (`progress_summary`), decision distribution (`decision_distribution`), and `next_pending_sample` for quick operator focus. Queue/manifest errors are returned as structured fields instead of breaking the operator main flow. |
| `/api/vision/review-decisions` | POST | Stores a manual review decision for one sample. Required fields: `sample_id`, `decision` (`approved`, `rejected`, `needs_retry`). Optional: `comment`, `option`, `operator`. |
| `/api/collect` | POST | Starts `/trashbot/collect_trash`. Optional JSON body or query parameter `target` overrides the default delivery target. |
| `/api/dropoff/confirm` | POST | Calls `/trashbot/confirm_dropoff`; optional JSON `accepted=false` rejects a pending manual dropoff. |
| `/api/cancel` | POST | Cancels the active `collect_trash` action goal if one is running. |

Every status-style response generated by the gateway includes:

| Field | Contract |
| --- | --- |
| `phone_copy` | Plain-language phone UI copy for the current state; clients should display this instead of parsing ROS-oriented status text. |
| `speaker_prompt` | Short prompt suitable for a speaker, buzzer/voice layer, or phone text-to-speech. |
| `phone_readiness` | `/api/status` aggregation for phone-first readiness. It is derived from local delivery status, action permissions, local/mock `remote_readiness`, optional cloud preflight, and optional backup/restore drill summaries. Older clients may ignore it. |
| `phone_support_bundle` | Phone-safe support handoff package for failed, blocked, waiting-ACK, or human-takeover states. It reuses the same status/readiness/diagnostics summaries and filters credentials, raw ROS topics, motion-control internals, hardware parameters, local paths, tracebacks, checksums, and complete artifacts. |
| `operation_log` / `phone_operation_log` | Phone-safe operation/support event metadata for recent user actions, blocked reasons, pending ACK, offline/recovery, manual takeover, and support handoff. It is not a ROS2 action, service, topic, ACK, cursor, Nav2/fixed-route result, WAVE ROVER feedback, or delivery-success surface. |
| `mobile_action_confirmation` / `mobile_action_receipt` / `phone_action_feedback` | Phone-safe action confirmation and receipt metadata for Start/Confirm/Cancel UI feedback. These fields summarize accepted/processing state, blocked reasons, or recovery copy for the phone; they are not `trashbot.remote.v1` command/status/ACK envelope fields and must not trigger robot actions, ACK, cursor updates, or delivery-success claims. |
| `mobile_device_acceptance_readiness` / `phone_device_acceptance_readiness` / `mobile_browser_acceptance_readiness` | Phone/browser acceptance metadata for device/browser readiness panels. These fields are support metadata only: they are not `trashbot.remote.v1` command/status/ACK envelope fields, not ROS2 actions or services, and must not trigger `/trashbot/collect_trash`, `/trashbot/confirm_dropoff`, cancel, ACK POSTs, cursor updates, or delivery-success claims. |
| `mobile_browser_acceptance_bundle` / `phone_browser_acceptance_bundle` / `mobile_acceptance_evidence_bundle` | Phone/browser acceptance-bundle metadata for browser viewport, touch, PWA/offline, diagnostics, cloud/action gates, safe copy, and evidence-boundary summaries. These fields are consumed by mobile UI and diagnostics only; the robot control loop must ignore them and must not turn them into commands, status, ACK, cursor, hardware, HIL, or delivery-success evidence. |
| `oss_cdn_live_probe` / `oss_cdn_live_probe_artifact` / `cdn_live_probe` | Phone/support metadata for OSS/CDN live probe readiness. These fields may summarize blocked probe status, redacted endpoint/object evidence, and recovery copy, but they are not `trashbot.remote.v1` command/status/ACK envelope fields and must not trigger `/trashbot/collect_trash`, `/trashbot/confirm_dropoff`, cancel, ACK POSTs, cursor updates, persisted `last_terminal_ack_id`, or delivery-success claims. |
| `voice_prompt_readiness` | Phone-safe prompt readiness package for the current `speaker_prompt`/elevator-assist prompt. It is exposed at top-level `/api/status`, nested as `phone_readiness.voice_prompt_readiness`, and mirrored in `/api/diagnostics.voice_prompt_readiness`. |
| `phone_offline_resume_readiness` | Phone-safe offline/resume package for reconnect, stale status, pending ACK, command safety, support handoff, offline shell behavior, and ACK semantics. It is exposed at top-level `/api/status`, nested as `phone_readiness.phone_offline_resume_readiness`, and mirrored in `/api/diagnostics.phone_offline_resume_readiness`. |

### Mobile Web Consumer

`mobile/web/` is the dependency-free phone PWA consumer for the operator/remote phone-safe contract. It is a consumer only and does not change ROS2 action, service, topic, or `trashbot.remote.v1` command/status/ack semantics.

Runtime files:

| File | Contract |
| --- | --- |
| `mobile/web/index.html` | Phone-first static entrypoint. It starts with primary actions disabled and waits for `/api/status`. |
| `mobile/web/app.js` | Reads `/api/status` and `/api/diagnostics`; renders `phone_readiness`, `command_safety`, `phone_offline_resume_readiness`, optional task-flow/support/voice summaries, and sanitized diagnostics fields. |
| `mobile/web/manifest.webmanifest` | PWA metadata for the static shell. `evidence_boundary=software_proof_docker_mobile_web_entrypoint_gate`. |
| `mobile/web/service-worker.js` | Caches only static shell files and bypasses dynamic control traffic. |
| `mobile/web/offline.html` | Offline recovery shell. Start Delivery, Confirm Dropoff, and Cancel remain disabled. |
| `mobile/fixtures/mobile_web_status.fixture.json` | Static smoke fixture only; must remain marked `fixture=true` and must not be treated as live robot state. |

Button enablement contract:

| Button | Required backend allowance |
| --- | --- |
| Start Delivery | `phone_readiness.command_safety.actions.start.enabled=true` and `action_permissions.can_collect=true` or top-level `can_collect=true`. |
| Confirm Dropoff | `phone_readiness.command_safety.actions.confirm_dropoff.enabled=true` and `action_permissions.can_confirm_dropoff=true` or top-level `can_confirm_dropoff=true`. |
| Cancel | `phone_readiness.command_safety.actions.cancel.enabled=true` and `action_permissions.can_cancel=true` or top-level `can_cancel=true`. |
| Diagnostics / Support Handoff | May stay accessible while primary actions are blocked; opening them must not trigger robot actions. |

Fail-closed rule: when `command_safety` is missing, stale, blocked, waiting for ACK, offline, or manual takeover is required, the mobile web entrypoint keeps Start Delivery, Confirm Dropoff, and Cancel disabled. ACK copy remains command accepted/processing evidence only and must not be rendered as delivery success.

Service-worker boundary:

| Traffic | Cache behavior |
| --- | --- |
| Static shell (`index.html`, CSS, JS, manifest, offline shell, icons) | May be cached. |
| `/api/*`, `/robots/*`, command routes, ACK routes, diagnostics, and every non-GET request | Must bypass cache with `no-store`. |

Evidence boundary: `software_proof_docker_mobile_web_entrypoint_gate`. It does not prove production app readiness, real phone-device/browser acceptance, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or delivery success.

`phone_readiness` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.phone_readiness.v1`. |
| `schema_version` | Integer schema version, currently `1`. |
| `evidence_boundary` | `software_proof_docker_local_phone_ui_readiness_gate`; this is local/Docker software proof only. |
| `primary_state` | One of the current phone-first states: `ready`, `local_ready_remote_status_waiting`, `waiting_for_robot_status`, `waiting_for_command_ack`, `login_required`, `remote_unreachable`, `remote_response_invalid`, `manual_takeover_required`, or `monitoring`. |
| `can_continue` | Whether the current phone journey has a safe next step. It does not prove delivery success. |
| `next_action` | Machine-readable recovery/action hint: `continue_local_flow`, `continue_local_or_wait_remote_status`, `wait_for_robot_status`, `wait_for_command_ack`, `check_auth`, `retry_cloud`, `contact_support`, `manual_takeover`, or `watch_progress`. |
| `safe_phone_copy` | User-facing readiness summary. Must not include raw JSON, credentials, ROS topic names, serial devices, baudrate, WAVE ROVER parameters, or `/cmd_vel`. |
| `recovery_hint` | User-facing next step. |
| `support_level` | Support classification for phone UI and operator support, such as `phone_ready`, `local_fallback`, `local_fallback_only`, `remote_blocked`, `remote_waiting_status`, `remote_waiting_ack`, `support_required`, or `human_takeover_required`. |
| `local_delivery` | Current local state plus `phone_copy` and `speaker_prompt`. |
| `action_permissions` | Copies `can_collect`, `can_confirm_dropoff`, and `can_cancel`. These remain the source for button enablement. |
| `remote_readiness` | Pass-through local/mock remote readiness. |
| `cloud_preflight` | Optional phone-safe preflight summary. Missing data maps to `not_run` or `unknown`; it is not a robot delivery failure. |
| `backup_restore` | Optional phone-safe backup/restore drill summary. Missing data maps to `not_run` or `unknown`; it is not disaster recovery proof. |
| `phone_support_bundle` | Same object exposed at top-level `/api/status.phone_support_bundle`; nested here so clients that only consume readiness can still show Support Handoff. Schema is `trashbot.phone_support_bundle.v1`, evidence boundary is `software_proof_docker_phone_support_bundle_gate`. |
| `voice_prompt_readiness` | Same object exposed at top-level `/api/status.voice_prompt_readiness`; nested here so clients that only consume readiness can show the current prompt, trigger, human-help requirement, playback boundary, ACK semantics, and not-proven list. Schema is `trashbot.voice_prompt_readiness.v1`, evidence boundary is `software_proof_docker_phone_voice_prompt_readiness_gate`. |
| `phone_offline_resume_readiness` | Same object exposed at top-level `/api/status.phone_offline_resume_readiness`; nested here so clients that only consume readiness can show reconnect/resume state, command safety result, support handoff availability, offline shell boundary, ACK semantics, and not-proven list. Schema is `trashbot.phone_offline_resume_readiness.v1`, evidence boundary is `software_proof_docker_phone_offline_resume_gate`. |
| `not_proven` | Explicit list of capabilities this local gate does not prove, including production phone app, real cloud/4G, OSS/CDN, Nav2/fixed-route delivery, WAVE ROVER motion, and HIL pass. |

ACK semantics remain separate from delivery result semantics. `remote_readiness.last_command_ack` or `degradation_state=ok` only says the command envelope was processed; phone clients must keep reading local or remote status for delivery progress, failure, cancellation, or human-takeover results.

`phone_support_bundle` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.phone_support_bundle.v1`. |
| `schema_version` | Integer schema version, currently `1`. |
| `evidence_boundary` | `software_proof_docker_phone_support_bundle_gate`; this is local/Docker software proof only. |
| `bundle_id` | Local tracking id. It must not contain tokens, paths, hardware parameters, serial details, or full artifact identifiers. |
| `generated_at` | Local generation timestamp. |
| `support_level` | Handoff classification, for example `phone_ready`, `local_fallback`, `remote_waiting_ack`, `support_required`, or `human_takeover_required`. |
| `status_summary` | Plain-language current state summary from `phone_readiness` or local status. |
| `failure_summary` | Plain-language terminal failure or blocking summary. If no terminal failure exists, it must say so instead of inventing one. |
| `next_steps` | User next step and support next step. |
| `ack_semantics` | Must state that ACK is accepted/processing evidence only and is not delivery success. |
| `support_refs` | Sanitized short references such as software/map/route version, failure code, current step, support level, and command block reason. |
| `safe_copy` | Chinese-first text block safe for copy/paste to family, after-sales, or engineering support. |
| `not_proven` | Explicit non-claims including real phone device, production app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route, WAVE ROVER, HIL, ACK-as-delivery-success, and delivery success. |

`phone_support_bundle` must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB or queue URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums, or complete artifacts. `/api/diagnostics.phone_support_bundle` uses the same builder as `/api/status`, but may add sanitized failure context from diagnostics. Opening Support Handoff or Diagnostics must not trigger robot actions.

`operation_log` / `phone_operation_log` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.phone_operation_log.v1` or a compatible phone-support metadata schema. |
| `evidence_boundary` | `software_proof_docker_mobile_operation_log_gate` when produced by the local/Docker mobile operation-log gate. |
| `events` | Phone-safe recent event summaries such as user action, blocked reason, pending ACK, offline/recovering, manual takeover, or support handoff. |
| `safe_phone_copy` / `recovery_hint` | Chinese-first user copy and next step. These must not expose raw JSON, tokens, ROS topics, serial devices, baudrate, WAVE ROVER parameters, local paths, tracebacks, checksums, or complete artifacts. |
| `ack_semantics` | Must preserve that ACK is accepted/processing evidence only and is not delivery success. |
| `support_handoff` | Sanitized support entry metadata. Opening or rendering it must not trigger Start Delivery, Confirm Dropoff, Cancel, or any backend action. |
| `not_proven` | Must include the remaining non-claims: real phone device/browser, production app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route, WAVE ROVER, HIL, and delivery success. |

If operation-log metadata appears beside a cloud `command` response or in any status/diagnostics payload, robot-side code must treat it as ignorable phone/support metadata. A metadata-only response with no valid `trashbot.remote.v1` command must not call `/trashbot/collect_trash`, `/trashbot/confirm_dropoff`, or cancel; must not POST ACK; and must not advance or persist `last_terminal_ack_id`.

`mobile_device_acceptance_readiness`, `phone_device_acceptance_readiness`, and `mobile_browser_acceptance_readiness` follow the same robot-side metadata-only rule. They may describe phone-device acceptance, browser acceptance, diagnostics availability, support handoff, and safe user copy, but they are not command, status, ACK, or cursor inputs. If any of these fields appear beside a valid `command`, the robot bridge must normalize and execute only that command envelope. If they appear without a valid command, the bridge must leave `/trashbot/collect_trash`, `/trashbot/confirm_dropoff`, cancel, ACK POSTs, `last_ack_id`, and persisted `last_terminal_ack_id` unchanged. ACK remains accepted/processing evidence only; it is never delivery success, phone-device acceptance proof, or browser acceptance proof.

`mobile_browser_acceptance_bundle`, `phone_browser_acceptance_bundle`, and
`mobile_acceptance_evidence_bundle` extend the same phone/support metadata
boundary for browser acceptance. They may summarize viewport, touch-target,
PWA install prompt, offline shell, diagnostics, cloud/action gates, client
timestamp, safe phone copy, redacted evidence refs, and `not_proven` items for
mobile UI or diagnostics. They are not `trashbot.remote.v1`
command/status/ACK envelope fields, ROS2 action/service inputs, backend action
results, cursor instructions, Nav2/fixed-route results, WAVE ROVER feedback,
HIL evidence, production-app readiness, real browser acceptance, or delivery
success proof. If they appear beside a valid `command`, robot-side
normalization must strip the bundle fields and execute only the valid command
envelope. If they appear without a valid command, the bridge must not invoke
`collect`, `confirm_dropoff`, or `cancel`, must not POST ACK, and must not
advance in-memory `last_ack_id` or persist `last_terminal_ack_id`.
`trigger_robot_action`, `next_action`, `cursor_override`,
`delivery_success`, raw ROS topics, `/cmd_vel`, serial devices, hardware
parameters, Authorization headers, credentials, local paths, tracebacks,
checksums, and complete artifacts must not be copied into robot status, ACK,
backend action result, or normalized command payload. ACK remains
accepted/processing evidence only; it is never delivery success or acceptance
completion.

`cloud_public_ingress_tls`, `public_ingress_tls`, `cloud_public_ingress_tls_gate`, and public-ingress/TLS details under `deployment_readiness` are deployment readiness metadata only. They may describe whether a public ingress, TLS config, reverse proxy config, or external probe artifact is present, but they are not robot commands and do not alter the `trashbot.remote.v1` command/status/ACK envelope. If those fields appear without a valid `command`, robot-side code must not call backend actions, must not POST ACK, must not advance or persist cursor state, and must not copy `delivery_success`, `cursor_override`, Authorization/token material, credential-bearing URLs, raw ROS topics, `/cmd_vel`, serial devices, or hardware parameters into status or ACK. ACK remains accepted/processing evidence only; it is never delivery success or proof of real HTTPS/TLS/public ingress.

`voice_prompt_readiness` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.voice_prompt_readiness.v1`. |
| `schema_version` | Integer schema version, currently `1`. |
| `evidence_boundary` | `software_proof_docker_phone_voice_prompt_readiness_gate`; this is local/Docker prompt-contract proof only. |
| `current_prompt` | Current prompt that the phone may display or a future speaker/TTS layer may play. Chinese is preferred when a Chinese prompt exists. |
| `prompt_language` | Prompt language tag such as `zh-CN` or `en-US`. |
| `trigger_state` | State that selected the prompt, for example `waiting_for_trash`, `requesting_floor_help`, `target_floor_unconfirmed`, `unsafe_to_exit`, `failed`, or `needs_human_help`. |
| `trigger_reason` | Phone-safe plain-language reason for the prompt. |
| `requires_human_help` | True when user, bystander, support, or operator intervention is required. |
| `playback_ready` | Must remain `false` for the local/Docker proof; this gate does not prove real speaker or TTS playback. |
| `safe_phone_copy` | Chinese-first copy for the first screen. It must state that ACK is accepted/processing evidence only and that prompt readiness is not actual playback proof. |
| `ack_semantics` | Must state that ACK is not delivery success and not proof that the prompt was played. |
| `support_refs` | Sanitized short references such as state, failure code, support level, and command block reason. |
| `not_proven` | Explicit non-claims including real speaker playback, TTS playback, microphone wake word, real phone device, production phone app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, and delivery success. |

When elevator assisted delivery reaches `requesting_floor_help`, `current_prompt` must be:

```text
你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,
```

`voice_prompt_readiness` must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB or queue URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums, or complete artifacts. Opening Diagnostics or reading this summary must not trigger robot actions and must not alter `trashbot.remote.v1` command/status/ack envelope semantics.

`phone_offline_resume_readiness` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.phone_offline_resume_readiness.v1`. |
| `schema_version` | Integer schema version, currently `1`. |
| `evidence_boundary` | `software_proof_docker_phone_offline_resume_gate`; this is local/Docker offline/resume proof only. |
| `connection_state` | Phone recovery state: `offline`, `status_stale`, `pending_ack`, `blocked`, `manual_takeover`, `recovering`, or `online`. |
| `can_resume` | True only when connection state is online and command safety allows at least one primary action. |
| `primary_actions_enabled` | Whether Start Delivery, Confirm Dropoff, or Cancel is currently enabled after command safety. |
| `support_entry_enabled` | Whether Diagnostics or Support Handoff can still be opened while primary actions are blocked. |
| `next_action` | Machine-readable recovery hint such as `wait_reconnect`, `wait_for_robot_status`, `wait_for_command_ack`, `retry_cloud`, `manual_takeover`, or `continue_local_flow`. |
| `safe_phone_copy` | Chinese-first user copy for the first-screen offline/resume panel. |
| `recovery_hint` | User-facing recovery step after reconnect, stale status, pending ACK, or manual takeover. |
| `ack_semantics` | Must state that ACK is accepted/processing evidence only and is not delivery success. |
| `support_handoff` | Sanitized support handoff availability and copy. |
| `voice_prompt` | Prompt readiness boundary summary; local/Docker proof does not prove real speaker/TTS playback. |
| `command_safety` | Compact summary of the final browser button gate, including `global_block_reason`, primary-action state, and diagnostics availability. |
| `offline_shell` | Confirms Start/Confirm/Cancel remain disabled and no control request cache is used in the offline shell. |
| `not_proven` | Explicit non-claims including real phone browser/device, production app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route, WAVE ROVER motion, HIL, and delivery success. |

`phone_offline_resume_readiness` must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB or queue URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, local filesystem paths, checksums, or complete artifacts. Opening Diagnostics, Support Handoff, or the offline shell must not trigger robot actions, must not cache control requests, and must not alter `trashbot.remote.v1` command/status/ack envelope semantics.

The same `/api/status` payload carries live location telemetry when available:

| Field | Contract |
| --- | --- |
| `robot_pose` | Latest `/amcl_pose` sample as `frame_id`, `x`, `y`, `yaw`, and `updated_at`. `null` until pose data arrives. |
| `robot_location` | Compatibility alias for `robot_pose`. |
| `robot_path` | Recent pose trail, capped at 200 points, for the browser trajectory view. |

| Parameter | Default | Contract |
| --- | --- | --- |
| `pose_topic` | `/amcl_pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` topic used for the local web location view. |
| `software_version` | installed package version or `0.1.0` fallback | Version reported in `/api/diagnostics`. |
| `map_version` | empty | Map version label reported in `/api/diagnostics`; route/map generation should set this when available. |
| `route_version` | empty | Route version label reported in `/api/diagnostics`; fixed-route tooling should set this when available. |
| `log_refs` | empty list | Operator-facing log references included in `/api/diagnostics`. |
| `vision_sample_manifest_ref` | `~/.ros/trashbot_vision_samples/manifest.json` | Optional deployment-supplied reference for future vision samples; the current MVP does not ship a default detector or manifest producer. |
| `review_decision_log_ref` | `~/.ros/trashbot_vision_samples/review_decisions.jsonl` | Local JSONL sink for manual review decisions. Missing/corrupt decision logs are reported through structured diagnostics fields. |
| `hardware_proof_ref` | empty | Optional software-proof artifact path consumed by `/api/diagnostics.hardware_proof`. Empty or unreadable paths must degrade to `read_error`; this evidence is software-only and is never equivalent to HIL pass. |

Launch entry mapping:

- `bringup.launch.py` and `autonomous.launch.py` expose `operator_hardware_proof_ref`.
- That launch argument maps 1:1 to operator gateway node parameter `hardware_proof_ref`.

`/api/diagnostics.vision_samples` keeps the legacy summary fields (`manifest_ref`, `exists`, `schema`, `sample_count`, latest sample fields, `event_counts`, `review_queue`, and `read_error`) and adds manifest integrity fields produced from `ros2_trashbot_vision.vision_sample_manifest.summarize_manifest()` when available:

| Field | Contract |
| --- | --- |
| `integrity_summary.status` | `ok`, `warning`, `error`, `not_configured`, `checker_unavailable`, or `checker_failed`; phone and support tools can use this as the high-level sample-chain health state. |
| `integrity_error_count` / `integrity_warning_count` | Counts of checker errors and warnings. Errors mean required manifest shape or required file references are not trustworthy; warnings mean optional evidence or schema expectations need review. |
| `integrity_errors` / `integrity_warnings` | Checker messages for remote support. These are diagnostic strings, not user-facing phone copy. |
| `missing_file_ref_count` / `missing_file_refs` | Count and detail list for manifest references that could not be resolved or found, including `sample_index`, field name, original value, and resolved path when available. |
| `context_field_coverage` | Per-context-field present/missing counts for `task_id`, `route_id`, `checkpoint_id`, `event_type`, and `anomaly_type`. |
| `file_counts` | Per-reference present/missing/empty counts for `sample_ref`, `json`, `raw_image`, and `annotated_image`. |

If the manifest is not configured or the vision checker cannot be imported, diagnostics still returns HTTP payloads with the legacy fields and a structured integrity fallback instead of failing the whole endpoint.

`/api/diagnostics.route_proof_summary` is consumed from navigation proof output only (pass-through/mapping on behavior side). Behavior/operator must not recalculate coverage logic from local samples:

| Field | Contract |
| --- | --- |
| `route_proof_summary.coverage_rate` | Nav proof source-of-truth ratio. Behavior side only reads and displays it. |
| `route_proof_summary.covered_checkpoints` | Nav proof source-of-truth covered count. |
| `route_proof_summary.total_checkpoints` | Nav proof source-of-truth route checkpoint count. |
| `route_proof_summary.missing_checkpoints` | Nav proof source-of-truth missing checkpoint IDs/names. |
| `route_proof_summary.gate_status` | Nav proof source-of-truth visual gate status. |
| `route_proof_summary.last_block_reason` | Nav proof source-of-truth block reason text. |

`/api/diagnostics.route_proof_status` is a behavior-side readable classification derived from the above fields only:

| Field | Contract |
| --- | --- |
| `route_proof_status.state` | One of `ready`, `waiting_visual_gate`, `insufficient_coverage`, `blocked`, `unknown`. |
| `route_proof_status.reason` | Human-readable mapped explanation for the current state. |
| `route_proof_status.blocking_reason` | Non-empty only when state is `blocked`; sourced from `route_proof_summary.last_block_reason`. |
| `route_proof_status.missing_fields` | Required fields that were missing in `route_proof_summary`; non-empty implies `state=unknown`. |
| `route_proof_status.source` | Where behavior consumed the proof (`latest_status`, `last_task`, or task record evidence). |

`route_proof_status.state` mapping rule (single behavior-side contract, no local recomputation):

| State | Mapping condition |
| --- | --- |
| `unknown` | `route_proof_summary` missing, required fields missing, `coverage_rate` is non-numeric, or unsupported `gate_status`. |
| `waiting_visual_gate` | `gate_status` in `{waiting_visual_gate, waiting, pending, blocked_by_visual_gate, waiting_camera_frame, missing_live_frame, keyframe_preflight_failed, missing_keyframe, no_live_descriptors, insufficient_matches}`. This check runs before generic `blocked` mapping to preserve nav visual-gate waiting semantics. |
| `blocked` | `last_block_reason` is non-empty and `gate_status` is not one of the waiting statuses above. |
| `insufficient_coverage` | `coverage_rate < 1.0` or `missing_checkpoints` still has values after field validation. |
| `ready` | `coverage_rate >= 1.0`, `missing_checkpoints` empty, and `gate_status` in `{passed, ready, ok}`. |

`review_queue` items include manual-review merge fields:

| Field | Contract |
| --- | --- |
| `review_status` | `pending` or `decided`; derived from decision-log merge, not from UI-local state. |
| `last_decision` | `null` or latest decision summary (`decision_id`, `decision`, `comment`, `option`, `operator`, `timestamp`). |

Review progress aggregates are exposed by both `/api/vision/review-queue` and `/api/diagnostics.vision_samples`:

| Field | Contract |
| --- | --- |
| `progress_summary.total` | Number of reviewable samples based on current manifest queue criteria. |
| `progress_summary.decided` | Number of reviewable samples that have a valid latest decision. Duplicate records for one sample use last-valid-decision semantics. |
| `progress_summary.pending` | `max(total - decided, 0)`. |
| `progress_summary.coverage_rate` | `decided / total` rounded to 4 decimals; returns `0.0` when `total=0`. |
| `decision_distribution.<decision>.count` | Final-decision count per decision type (`approved`, `rejected`, `needs_retry`) among decided samples. |
| `decision_distribution.<decision>.ratio` | `count / decided` rounded to 4 decimals; returns `0.0` when `decided=0`. |
| `next_pending_sample` | `null` when there is no pending sample; otherwise includes `sample_id`, `sample_ref`, `reason`, `event_type`, and `timestamp`. |

`/api/diagnostics.review_decision_log` and `/api/vision/review-queue.review_decision_log` expose decision-store health:

| Field | Contract |
| --- | --- |
| `status` | `ok`, `not_configured`, `missing`, or `read_error`. |
| `decision_log_ref` | Resolved decision JSONL path. |
| `exists` | Whether the decision log exists. |
| `decision_count` / `sample_count` | Valid decision rows and distinct sample IDs in the log. |
| `read_error` | Structured read/parsing error detail when unavailable or malformed. |

`/api/diagnostics.hardware_proof` summarizes an offline artifact produced by `ros2_trashbot_hardware.hardware_diagnostics_proof`. The artifact source remains hardware-owned and vendor-backed by `docs/vendor/VENDOR_INDEX.md`; the operator gateway only reads it and maps it into phone-safe support states. Software proof is not HIL pass, hardware pass, real UART validation, wheel-direction validation, speed-unit validation, feedback-frequency measurement, IMU validation, or battery validation.

| Field | Contract |
| --- | --- |
| `status` | One of `software_proof`, `needs_hil`, `invalid_config`, or `read_error`. Unknown, missing, malformed, or unreadable artifacts must map conservatively and must not make `/api/diagnostics` fail. |
| `artifact_ref` | Path or deployment reference used to read the artifact. Empty means no artifact is configured. |
| `source_status` | Raw artifact status, such as `software_proof_ready`, `invalid_config`, or `feedback_parse_failed`. |
| `exists` | Whether the artifact path existed and could be opened far enough for the summary attempt. |
| `read_error` | Structured read/config/parsing problem. This field is populated for missing files, bad JSON, non-object JSON, missing status, unsupported status, invalid config detail, or feedback-parse failure. |
| `summary` | Phone/support copy. It must remain conservative and must never claim hardware passed or HIL passed. |
| `next_step` | Recovery or validation action, such as rerunning software proof, fixing bridge config, or running WAVE ROVER HIL. |
| `vendor_sources` | Vendor source references copied from the artifact. The operator gateway must not invent new hardware facts here. |
| `risk_flags` | Risk flags copied from the artifact. `hil_required` or high-severity HIL risk maps `software_proof_ready` to `needs_hil`. |
| `hil_recipe` | HIL recipe copied from the artifact for support/engineering validation. |

Status mapping:

| Artifact condition | Product status |
| --- | --- |
| `status=software_proof_ready` with `hil_required` or high HIL risk | `needs_hil` |
| `status=software_proof_ready` without HIL risk | `software_proof`, with copy that still says software proof only |
| `status=invalid_config` | `invalid_config` |
| `status=feedback_parse_failed` | `needs_hil` or `read_error`; current gateway uses `needs_hil` with read-error detail |
| Missing path, missing file, unreadable file, bad JSON, non-object JSON, missing status, unsupported status | `read_error` |

### 4G Remote Bridge

The optional `remote_bridge` node is the formal 4G-oriented remote MVP path. It does not expose robot-local HTTP to the phone. Instead, the robot initiates outbound HTTP polling to a cloud or mock-cloud endpoint. It is disabled by default in launch files and is intended to be testable without a real cloud account.

| Parameter | Default | Contract |
| --- | --- | --- |
| `enabled` | `false` | Runtime guard; launch also keeps the node off by default. |
| `cloud_base_url` | empty | Base URL for a mock or future cloud service. |
| `robot_id` | `trashbot-001` | Robot identity included in status and ack payloads. |
| `auth_token` | empty | Optional bearer token. When configured, robot-originated cloud requests use bearer auth; token values must never appear in status, diagnostics, ACK messages, or cursor state. |
| `poll_interval_sec` | `2.0` | Periodic command polling interval. |
| `request_timeout_sec` | `5.0` | HTTP request timeout. |
| `cursor_state_path` | empty | Optional file for persisted `last_terminal_ack_id`. It stores cursor metadata only and must not store bearer tokens, command payloads, serial devices, hardware parameters, or ROS topic names. |
| `last_ack_id` | empty | Launch-time fallback cursor used only when no valid `cursor_state_path` state is loaded. Treated as an opaque cloud cursor, not a sortable command id. |

| Direction | Endpoint | Contract |
| --- | --- | --- |
| robot -> cloud | `POST /robots/{robot_id}/status` | Sends the latest `trashbot.remote.v1` robot state before polling. |
| robot -> cloud | `GET /robots/{robot_id}/commands/next?last_ack_id=<id>` | Pulls `{"command": null}` or one command object. |
| robot -> cloud | `POST /robots/{robot_id}/commands/{command_id}/ack` | Sends `acked`, `failed`, or `ignored` plus local operator result metadata. `ignored` is used for expired commands that were not executed. |

Cloud responses may include optional status, preflight, diagnostics, queue,
mobile-web-entrypoint, PWA-entrypoint, voice-prompt-readiness,
production-recovery, transaction-isolation, cloud external probe,
cloud DB/queue external probe, OSS/CDN live probe, deployment-readiness, mobile
task-start confirmation, mobile action feedback, operation-log, DB/queue
config-gate, phone/mobile cloud-readiness summary, or mobile/browser
acceptance-bundle metadata beside the
`trashbot.remote.v1` command/status/ACK envelope. Robot clients must treat
those fields as ignorable diagnostics for forward compatibility. A
metadata-only response with `command=null` or no command object must not start a
robot action, must not emit ACK, and must not advance or persist
`last_terminal_ack_id`.
Cloud external probe metadata, including `cloud_external_probe` and
`cloud_external_probe_bundle`, is diagnostic/deployment metadata for
`/healthz`, `/readyz`, and `/preflightz` probe summaries. It is not a robot
command, delivery result, HIL result, or WAVE ROVER feedback. It may report
`production_ready=false`, `overall_status=blocked`, endpoint summaries, retry
hints, or redacted safe summaries, but it must not trigger `collect`,
`confirm_dropoff`, or `cancel`, post ACK, advance cursor state, persist
`last_terminal_ack_id`, or turn ACK copy into delivery success.
Deployment-readiness metadata, including `deployment_readiness`,
`cloud_deployment_readiness`, and `preflight`, is also deployment diagnostics
only; it is safe for older robot clients to ignore and cannot change
`trashbot.remote.v1` command normalization.
Mobile web entrypoint metadata, including `mobile_web_entrypoint`,
`mobile_web_entrypoint_readiness`, and `pwa_entrypoint`, is a phone/UI consumer
contract only. It may describe the static shell, installability, readiness, or
offline behavior, but it must not alter allowed remote command types, invoke
`collect`, `confirm_dropoff`, or `cancel`, post ACK, advance cursor state, or
turn ACK copy into delivery success.
Voice prompt readiness metadata is phone/operator prompt contract evidence only:
it must not trigger `collect`, `confirm_dropoff`, or `cancel`, and it must not
turn ACK into delivery success or proof that a speaker/TTS prompt was played.
Transaction-isolation metadata is proof about the cloud/control-plane drill
only; it is not a delivery result and cannot override ACK semantics.
Production-recovery metadata is phone/operator support metadata only. It may
describe local Docker recovery gate state, `production_ready=false`, or
`overall_status=blocked`, but it is not part of the remote command envelope, is
safe for older robot clients to ignore, and must not trigger `collect`,
`confirm_dropoff`, `cancel`, ACK emission, or cursor advancement on its own.
DB/queue config-gate metadata, including `cloud_db_queue_config`,
`cloud_db_queue_config_gate`, and `db_queue_config`, is phone-safe/cloud
readiness metadata for cloud database and queue configuration proof. It may
describe `production_ready=false`, blocked readiness, redacted config checks, or
software-proof evidence boundaries, but it is not a robot command, ACK payload,
status-post extension, backend action result, cursor instruction, ROS2 action
result, WAVE ROVER feedback, HIL result, or delivery success proof. Robot-side
protocol normalization must strip those fields from valid command objects, and
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, and must not advance or persist
`last_terminal_ack_id`. DB URLs, queue URLs, credentials, Authorization headers,
raw ROS topics, `/cmd_vel`, serial devices, hardware parameters,
`trigger_robot_action`, `cursor_override`, and `delivery_success` must not be
copied into robot status, ACK, backend action result, or normalized command
payload.
DB/queue external-probe metadata, including
`cloud_db_queue_external_probe`, `cloud_db_queue_external_probe_bundle`, and
`db_queue_external_probe`, is the follow-on readiness proof for externally
probing cloud database and queue dependencies. It may describe
`production_ready=false`, `overall_status=blocked`, redacted probe results,
retry hints, or the evidence boundary
`software_proof_docker_cloud_db_queue_external_probe_gate`, but it is not part
of the `trashbot.remote.v1` command/status/ACK envelope. It must not be treated
as a robot command, backend action result, ACK payload, cursor instruction,
ROS2 action result, WAVE ROVER feedback, HIL result, real production DB/queue
proof, or delivery success proof. Robot-side protocol normalization must strip
those fields from valid command objects, and metadata-only responses must not
invoke `collect`, `confirm_dropoff`, or `cancel`, must not POST ACK, and must
not advance or persist `last_terminal_ack_id`. DB/queue URLs, credentials,
Authorization headers, raw ROS topics, `/cmd_vel`, serial devices, hardware
parameters, `trigger_robot_action`, `cursor_override`, and `delivery_success`
must not be copied into robot status, ACK, backend action result, or normalized
command payload. ACK remains accepted/processing evidence only and must not be
interpreted as delivery success or external DB/queue production readiness.
OSS/CDN live-probe metadata, including `oss_cdn_live_probe`,
`oss_cdn_live_probe_artifact`, and `cdn_live_probe`, is phone/support readiness
metadata for checking whether future OSS object and CDN endpoint probes have
safe, redacted evidence. It may describe `production_ready=false`,
`overall_status=blocked`, redacted endpoint paths, object-key hashes, retry
hints, or the evidence boundary
`software_proof_docker_oss_cdn_live_probe_gate`, but it is not part of the
`trashbot.remote.v1` command/status/ACK envelope. It must not be treated as a
robot command, backend action result, ACK payload, cursor instruction, ROS2
action result, Nav2/fixed-route result, WAVE ROVER feedback, HIL result, real
OSS/CDN live traffic proof, or delivery success proof. Robot-side protocol
normalization must strip those fields from valid command objects, and
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, and must not advance or persist
`last_terminal_ack_id`. Credential URLs, Authorization headers, OSS AK/SK,
raw ROS topics, `/cmd_vel`, serial devices, hardware parameters,
`trigger_robot_action`, `cursor_override`, and `delivery_success` must not be
copied into robot status, ACK, backend action result, or normalized command
payload. ACK remains accepted/processing evidence only and must not be
interpreted as delivery success or real OSS/CDN production readiness.
Cloud-readiness summary metadata, including
`phone_cloud_readiness_summary`, `mobile_cloud_readiness_summary`, and
`cloud_readiness_summary`, is phone-safe support/readiness summary for the
mobile surface to explain cloud DB/queue/config readiness. It may summarize
blocked readiness, `production_ready=false`, redacted support copy, or the
software-proof boundary, but it is not part of the `trashbot.remote.v1`
command/status/ACK envelope. It is not a robot command, ACK payload, cursor
instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback,
HIL result, real cloud/4G proof, or delivery success proof. Robot-side protocol
normalization must strip those fields from valid command objects, and
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, and must not advance or persist
`last_terminal_ack_id`. Production-ready claims, credential material,
credential-bearing cloud URLs, raw ROS topics, `trigger_robot_action`,
`cursor_override`, and `delivery_success` must not be copied into robot status,
ACK, backend action result, or normalized command payload. ACK remains
accepted/processing evidence only and must not be interpreted as delivery
success.
Mobile task-start confirmation metadata, including
`mobile_task_start_confirmation`,
`mobile_task_start_confirmation_readiness`, and
`task_start_confirmation_payload`, is the phone/UI API record that a user
selected a destination and confirmed the trash was loaded before pressing Start
Delivery. It is not a ROS2 action result, HIL result, WAVE ROVER feedback, or
delivery success proof. The robot bridge must ignore those fields outside the
`trashbot.remote.v1` command envelope; only a valid `command.id`,
`command.type`, and `command.payload` may drive `collect`, `confirm_dropoff`, or
`cancel`.
Mobile action feedback metadata, including `mobile_action_confirmation`,
`mobile_action_receipt`, and `phone_action_feedback`, is the phone/UI support
summary for Start/Confirm/Cancel submission feedback. It may describe
accepted/processing copy, blocked reasons, recovery hints, client references,
and the evidence boundary
`software_proof_docker_mobile_action_feedback_gate`. It is not a
`trashbot.remote.v1` command/status/ACK envelope, ROS2 action result,
Nav2/fixed-route result, WAVE ROVER feedback, HIL result, cursor instruction,
or delivery success proof. The robot bridge must ignore those fields outside a
valid command object; protocol normalization must strip them before execution;
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, and must not advance or persist
`last_terminal_ack_id`. ACK remains accepted/processing evidence only and must
not be rendered or interpreted as delivery success.
Mobile/browser acceptance-bundle metadata, including
`mobile_browser_acceptance_bundle`, `phone_browser_acceptance_bundle`, and
`mobile_acceptance_evidence_bundle`, is the phone/UI and diagnostics package
for browser viewport, touch, PWA/offline, diagnostics, cloud/action gates,
client timestamp, safe copy, and evidence-boundary summaries. It may help a
mobile client explain why controls stay blocked, but it is not a
`trashbot.remote.v1` command/status/ACK envelope, ROS2 action result,
Nav2/fixed-route result, WAVE ROVER feedback, HIL result, production app
readiness proof, real browser acceptance proof, cursor instruction, or delivery
success proof. Robot-side protocol normalization must strip these fields from
valid command objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, and must not advance or
persist `last_terminal_ack_id`. ACK remains accepted/processing evidence only
and must not be rendered or interpreted as delivery success.
Operation-log metadata, including `operation_log` and `phone_operation_log`, is
phone/support metadata for recent events, blocked reasons, pending ACK,
offline/recovery state, manual takeover, and support handoff copy. It is not a
robot command, ACK, cursor instruction, ROS2 action result, WAVE ROVER feedback,
Nav2/fixed-route result, HIL result, or delivery success proof. The robot bridge
must ignore those fields outside the `trashbot.remote.v1` command envelope, and
protocol normalization must strip them from any command object before execution.

Allowed remote commands are `collect`, `confirm_dropoff`, and `cancel`. The bridge only calls behavior-layer ROS contracts and never exposes direct base velocity control.
For `collect`, `acked` means the command was accepted/submitted locally; final delivery success or failure is reported through later status payloads.

#### Remote readiness fields

`operator_gateway` local/mock cloud status and `remote_bridge` degraded status use
the same phone-safe readiness shape. These fields are a control-plane contract;
they are not hardware, Nav2, fixed-route, or delivery success evidence.

| Field | Contract |
| --- | --- |
| `remote_ready` | `true` only when the local/mock control-plane is healthy enough for the next phone step. It does not prove real cloud, 4G, HIL, or trash delivery. |
| `cloud_reachable` | Whether the configured cloud/mock endpoint is reachable for the current operation. |
| `auth_state` | One of the phone-safe auth states used by the current implementation, including `mock_not_required`, `required`, `authorized`, and `auth_failed`. |
| `degradation_state` | One of the phone-safe degradation states used by the current implementation, including `ok`, `status_stale`, `command_pending`, `auth_failed`, `cloud_unreachable`, and `malformed_response`. |
| `retry_hint` | Phone/operator recovery hint such as `ok`, `wait_for_robot_status`, `wait_for_command_ack`, `check_auth`, `retry_cloud`, or `contact_support`. |
| `safe_phone_copy` | Plain-language copy suitable for phone UI. It must not contain raw JSON, raw exceptions, bearer tokens, Authorization headers, `/cmd_vel`, ROS topic names, serial devices, baudrate, WAVE ROVER parameters, or cloud URLs with credentials. |

#### Failure and cursor contract

| Condition | Required behavior |
| --- | --- |
| Cloud unreachable while posting status or polling command | Publish or retain degraded status, do not execute a new local action from untrusted data, do not advance or persist terminal cursor. |
| HTTP 401/403 auth failure | Map to `auth_state=auth_failed`, `degradation_state=auth_failed`, and a phone-safe retry hint. Do not leak tokens or raw headers. |
| Malformed command/status/ACK response | Map to `degradation_state=malformed_response`; do not submit a local action goal, do not advance cursor, and do not fabricate successful ACK. |
| Terminal ACK post failure | Keep the local command result available for retry, but do not update `last_terminal_ack_id` in memory or in `cursor_state_path`. |
| Terminal ACK post success | Only then may the bridge advance `last_terminal_ack_id` and atomically persist cursor state. |

ACK remains a command-envelope processing state. It is never a delivery result
and must not be used to claim Nav2/fixed-route success, WAVE ROVER movement, or
HIL pass.

| Type | Payload | Local action |
| --- | --- | --- |
| `collect` | Required `target`, optional `trash_type` | Starts `/trashbot/collect_trash`; malformed commands without a non-empty `target` are failed before any local action goal is sent. |
| `confirm_dropoff` | optional `accepted` | Calls `/trashbot/confirm_dropoff`. |
| `cancel` | empty object | Cancels the active collection goal when one exists. |

### Task Record

Every success, cancellation, missing target, navigation failure, dropoff failure, and unsupported-mode failure writes a JSON task record with `started_at`, `ended_at`, `delivery_mode`, `target`, `return_target`, `nav_attempts`, `nav_results`, `dropoff_result`, `detection_snapshot_refs`, `config`, `final_status`, and `error_message`. `dropoff_result` records `success`, `result_code`, `message`, `source`, and `elapsed_sec`; `manual_confirm_timeout` and `manual_rejected` are failures.

### Terminal Diagnostics

`TrashCollection.Result` exposes machine-readable terminal diagnostics:

| Field | Contract |
| --- | --- |
| `error_code` | Empty on success. On failure/cancel, set from the terminal state-machine event, such as `timed_out`, `navigation_failed`, `dropoff_failed`, `return_failed`, or `canceled`. |
| `final_state` | Final delivery state-machine state, such as `idle` or `error`. Operator and remote status payloads propagate this field so phone/cloud clients do not need to parse human text. |
