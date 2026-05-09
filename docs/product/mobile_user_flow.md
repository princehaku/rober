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
- Arrived at station.
- Returning.
- Completed.
- Needs human help.

## Exception Handling

The phone UI should show plain-language messages:

- "Route is not ready."
- "Robot cannot find the trash station."
- "Navigation failed."
- "Please remove trash manually."
- "Robot stopped for safety."

Users should not need SSH, ROS2 commands, serial tools, or direct hardware debugging for the normal flow.

## Minimum Local API

The first operator gateway is intentionally small: an API-first local HTTP service plus a minimal browser page at `/`. It is enough for a phone browser on the robot network, but it is not a polished native app, does not include account/login flows, and does not replace hardware bringup checks.

- `GET /api/status`
- `POST /api/collect`
- `POST /api/dropoff/confirm`
- `POST /api/cancel`

This is enough for a phone page or local browser control surface to complete a dry-run task and drive the manual dropoff confirmation service.

The local page also shows live robot location when localization is publishing. `operator_gateway` subscribes to `/amcl_pose` by default and includes `robot_pose` plus recent `robot_path` points in `GET /api/status`; without AMCL data the controls still work, but the map panel waits for pose updates.

## 4G Remote MVP

The first 4G path is a robot-side outbound polling bridge, not a production account system. Start it only when needed with `remote_bridge:=true` and a mock or future `remote_cloud_base_url`; the default launch value is off.

The mock-cloud command set mirrors the local user journey:

- `collect` starts the behavior collection action.
- `confirm_dropoff` submits the manual dropoff confirmation.
- `cancel` requests cancellation of the active collection.

The robot posts status and command acknowledgements back to the cloud endpoint so the same flow can be tested offline before choosing a real cloud provider.

## 4G Remote Product Path

For a 4G robot, the formal phone path is cloud-mediated rather than phone-to-robot WiFi:

```text
phone web/app -> cloud API -> robot remote_bridge over outbound 4G HTTP polling -> ROS2 behavior
```

The local operator gateway remains a development and fallback entrypoint. The 4G MVP contract is documented in `docs/product/remote_4g_mvp.md`.
