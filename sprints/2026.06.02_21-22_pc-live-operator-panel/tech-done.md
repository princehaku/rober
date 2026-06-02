# O7 PC Live Operator Panel Tech Done

## Sprint Type

sprint_type: micro

## Actual Changes

- Added `GET /api/o7/live-operator-panel` with schema `trashbot.o7.live_operator_panel.v1`.
- Added O7 first-screen `PC Live Operator` UI for LiDAR/Radar status, camera entry, direction buttons and speed display.
- Kept all control paths fail-closed: `safe_to_control=false`, `sends_commands=false`, `robot_control_executed=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Direction buttons only update local blocked copy and do not call any control API.
- Added interface documentation in `docs/interfaces/o7_live_operator_panel.md` and product boundary update in `docs/product/pc_tools_workstation.md`.

## Upper Computer Facts

- SSH target: `root@192.168.1.11 -p 37878`.
- Camera service fact carried into the contract: `http://192.168.1.11:8088/`, current `health_status=not_listening_observed`, historical `video_source=/dev/video1`.
- Workstation API fact carried into the contract: `8787=not_listening_observed`.
- LiDAR/Radar remains blocked: `/dev/lidar=missing`, STC by-id identity unresolved, scan not proven, no fabricated point cloud.

## Deployment Result

- 8787 deployment is not claimed in this sprint note.
- Final SSH readonly check reached the host, but `ss -ltnp` showed no 8088/8787 listeners and `curl http://127.0.0.1:8088/health` returned connection refused.
- No long-running deployment was attempted in this收口 pass.

## Verification

Final收口 commands:

```bash
cd pc-tools/workstation && npm run test
# Test Files  2 passed (2)
# Tests  65 passed (65)

cd pc-tools/workstation && npm run build
# vite build: 37 modules transformed
# built successfully

cd pc-tools/workstation && npm run lint
# passed, no lint errors

git diff --check -- pc-tools/workstation/src/App.vue pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/server/catalog.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/server/o7LiveOperatorPanel.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7LiveOperatorPanel.vue pc-tools/workstation/src/styles.css pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_live_operator_panel.md docs/product/pc_tools_workstation.md sprints/2026.06.02_21-22_pc-live-operator-panel/tech-done.md
# passed, no whitespace errors
```

Rendered smoke:

- Page contains `PC Live Operator`.
- Page contains `LiDAR / Radar Signal`.
- Page contains `Forward`.
- Page contains `Stop`.
- Forward click only shows blocked copy and does not add a new `fetch` call.

SSH readonly check:

```bash
timeout 12 ssh -o BatchMode=yes -o ConnectTimeout=6 -p 37878 root@192.168.1.11 'uname -a; ss -ltnp | grep -E "8088|8787" || true; curl -fsS http://127.0.0.1:8088/health | head -c 500'
```

- Host reachable: `Linux op-z3-b6.home 6.1.31-sun50iw9 ... aarch64`.
- `8088` and `8787` were not listening in `ss -ltnp`.
- `curl http://127.0.0.1:8088/health` failed with connection refused.

## OKR Impact

- O7 should not be raised; keep it at about 97% because the PC panel is locally verified but the remote 8088/8787 services are offline.

## Remaining Risks

- `base_serial_identity_not_proven`
- `t1001_feedback_not_observed`
- `robot_ack_not_connected`
- Real LiDAR `/scan`, WAVE ROVER UART feedback, robot ACK, Nav2/ROS2 control and delivery success are not proven.
