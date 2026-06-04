# Tech Done: Runtime Material Runtime Hooks

## sprint_type

sprint_type: epic

## 实际改动

### Robot Software Engineer

- 在 `onboard/scripts/upper_robot_api.py` 新增只读 `POST /api/radar/scan-proof/refresh` 合同。
- 该入口只运行同目录 `o1_lidar_scan_proof_collector.py --once-json --expect-existing-topics --output runtime/lidar_scan_proof_latest.json`，并返回 `command_result`、`artifact_path`、`proof_summary`、`blockers_summary` 和固定安全字段。
- 新增 unit/aiohttp route coverage，避免 route 漂移成 404/405。
- 更新 `docs/interfaces/o7_upper_robot_api.md` 与 `docs/interfaces/lidar_ros2_closed_loop.md`。

### User Touchpoint Full-Stack Engineer

- 在 PC workstation 新增 `POST /api/o7/direct-upper/radar/scan-proof/refresh` 同源代理。
- UI 新增 `Refresh scan proof` operator 按钮，继续要求 operator confirmation 和 `evidence_ref`。
- Direct 卡展示 scan proof artifact/freshness/age/latest status/top blockers。
- 更新 shared contract、client helper、server adapter、UI、测试和 `docs/interfaces/o7_direct_upper_pc_api.md` / `docs/product/pc_tools_workstation.md`。

### Hardware Infra Engineer

- 读取 vendor 资料并复核只读 scan proof refresh/readback 边界。
- 更新 `docs/hardware/o1_wave_rover_serial_feedback_probe.md` 和 `docs/interfaces/lidar_ros2_closed_loop.md`，明确 `T=1001` 是 vendor feedback material，不等于 robot ACK/HIL。
- 通过 SSH 只读回放确认当前 latest scan proof 和 base feedback samples 均保持 `safe_to_control=false`、`hil_pass=false`。

## 验证结果

### Robot Software

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
```

```text
Ran 28 tests in 1.761s
OK (skipped=2)
```

```bash
python3 -m compileall -q onboard/scripts
```

```text
passed with no output
```

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/o7_upper_robot_api.md docs/interfaces/lidar_ros2_closed_loop.md sprints/2026.06.04_21-22_runtime-material-runtime-hooks/owner_notes/robot-software-engineer.md
```

```text
passed with no output
```

SSH 只读验证：

```text
GET /health -> HTTP 200, status=ready, safe_to_control=false, robot_control_executed=false
GET /api/radar/status -> HTTP 200, scan_status=not_proven
GET /api/radar/status -> controls_keys=["start", "stop"]
GET /api/radar/status -> has_scan_proof_refresh_control=false
```

### Full-Stack

```bash
cd pc-tools/workstation && npm test -- --run
```

```text
Test Files  3 passed (3)
Tests  99 passed (99)
```

```bash
cd pc-tools/workstation && npm run build
```

```text
tsc + vite build + server tsc completed
```

```bash
cd pc-tools/workstation && npm run lint
```

```text
eslint . passed with no errors
```

```bash
git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7DirectUpperApi.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7LiveOperatorPanel.vue pc-tools/workstation/test/App.test.ts docs/interfaces/o7_direct_upper_pc_api.md docs/product/pc_tools_workstation.md sprints/2026.06.04_21-22_runtime-material-runtime-hooks/owner_notes/full-stack-software-engineer.md
```

```text
passed with no output
```

现场 8787 smoke：

```text
GET http://192.168.1.11:8787/health -> HTTP 200, status=ready, safe_to_control=false
POST http://192.168.1.11:8787/api/radar/scan-proof/refresh -> HTTP 405 Method Not Allowed, Allow=OPTIONS
```

### Hardware

```text
SSH 只读 GET /health、/api/status、/api/radar/status、/api/radar/scan-proof/latest、/api/base/status、/api/base/feedback-samples/latest
未调用 /api/base/manual、/api/base/feedback-request、/api/base/feedback-samples
未发送 T=1/T=13/T=130/T=131，未发布 /cmd_vel
```

```bash
git diff --check -- docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/hardware/o1_pc_manual_lidar_hil_boundary.md docs/interfaces/lidar_ros2_closed_loop.md sprints/2026.06.04_21-22_runtime-material-runtime-hooks/owner_notes/robot-hardware-engineer.md
```

```text
passed with no output
```

## 偏差和失败定位

- 本地 software contract 和 PC operator workflow 已完成并验证。
- 现场上位机 8787 仍未加载新 route：Software 只读状态显示 radar controls 只有 `start/stop`；Full-Stack 直接 POST `/api/radar/scan-proof/refresh` 返回 HTTP 405。
- 因 running 8787 reload path 未在本轮确认，未杀进程、未重启未知服务、未伪造 refresh 成功。

## 剩余风险

- 不证明 fresh `/scan` once/hz、`/lidar/raw_packet` once、TF、SLAM `/map`、AMCL、Nav2 lifecycle 或 route execution。
- 不证明 PC WASD、底盘 HIL、robot ACK、`safe_to_control=true` 或 delivery success。
- 下一步必须把本地 upper API / PC adapter 同步到上位机与 PC dev/runtime，并用明确安全 reload 路径重新验证 refresh route。
