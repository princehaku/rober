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
| `/api/diagnostics` | GET | Returns the minimum remote-support diagnostic package: software version, map/route versions, latest status, last task summary, terminal failure fields, log references, vision sample manifest reference, hardware proof summary, and operator status file path. |
| `/api/vision/review-queue` | GET | Returns review queue samples with `review_status` and `last_decision` summary. Queue/manifest errors are returned as structured fields instead of breaking the operator main flow. |
| `/api/vision/review-decisions` | POST | Stores a manual review decision for one sample. Required fields: `sample_id`, `decision` (`approved`, `rejected`, `needs_retry`). Optional: `comment`, `option`, `operator`. |
| `/api/collect` | POST | Starts `/trashbot/collect_trash`. Optional JSON body or query parameter `target` overrides the default delivery target. |
| `/api/dropoff/confirm` | POST | Calls `/trashbot/confirm_dropoff`; optional JSON `accepted=false` rejects a pending manual dropoff. |
| `/api/cancel` | POST | Cancels the active `collect_trash` action goal if one is running. |

Every status-style response generated by the gateway includes:

| Field | Contract |
| --- | --- |
| `phone_copy` | Plain-language phone UI copy for the current state; clients should display this instead of parsing ROS-oriented status text. |
| `speaker_prompt` | Short prompt suitable for a speaker, buzzer/voice layer, or phone text-to-speech. |

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

`review_queue` items include manual-review merge fields:

| Field | Contract |
| --- | --- |
| `review_status` | `pending` or `decided`; derived from decision-log merge, not from UI-local state. |
| `last_decision` | `null` or latest decision summary (`decision_id`, `decision`, `comment`, `option`, `operator`, `timestamp`). |

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
| `auth_token` | empty | Optional bearer token. |
| `poll_interval_sec` | `2.0` | Periodic command polling interval. |
| `request_timeout_sec` | `5.0` | HTTP request timeout. |

| Direction | Endpoint | Contract |
| --- | --- | --- |
| robot -> cloud | `POST /robots/{robot_id}/status` | Sends the latest `trashbot.remote.v1` robot state before polling. |
| robot -> cloud | `GET /robots/{robot_id}/commands/next?last_ack_id=<id>` | Pulls `{"command": null}` or one command object. |
| robot -> cloud | `POST /robots/{robot_id}/commands/{command_id}/ack` | Sends `acked`, `failed`, or `ignored` plus local operator result metadata. `ignored` is used for expired commands that were not executed. |

Allowed remote commands are `collect`, `confirm_dropoff`, and `cancel`. The bridge only calls behavior-layer ROS contracts and never exposes direct base velocity control.
For `collect`, `acked` means the command was accepted/submitted locally; final delivery success or failure is reported through later status payloads.

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
