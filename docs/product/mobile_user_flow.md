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

`GET /api/diagnostics` is the minimum support package for phone UI and remote support. It reports software version, map and route version labels, latest status, last task summary, machine-readable failure fields, log references, the operator status file, and the vision sample manifest reference. It does not claim that those files exist; it gives support tools stable references to inspect.

The local browser page is phone-first and uses the API fields directly: task state, `phone_copy`, `speaker_prompt`, action permissions, robot pose/path, and diagnostics. The page is still intentionally dependency-free HTML served by `operator_gateway`; it is a usable local control surface, not a production account system.

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
