# Tech Done: Runtime Material Deploy Refresh

## sprint_type

sprint_type: epic

## 实际改动

### Robot Software Engineer

- 远端同步 `upper_robot_api.py` 和 scan proof collector 到 `/root/rober/onboard/scripts/`。
- 创建远端备份目录 `/root/rober/runtime/deploy_backups/20260604T221619+0800`。
- 精确匹配旧游离 upper API PID `30042` 后发送 SIGTERM，并通过 `systemctl start trashbot-upper-robot-api.service` 拉起 Main PID `38154`。
- live 8787 refresh route 从 HTTP 405 变为 HTTP 200，`GET /api/radar/scan-proof/latest` 可加载 artifact。
- 修复 collector 在 systemd 子进程环境下缺 `HOME/USER/LOGNAME/ROS_LOG_DIR` 导致 ROS2 logging 初始化失败的问题；远端同步后本地/远端 hash 均为 `7175ec89c6ebcc18bca22414f58029cd3504aaecdd1b4bb0aa11d376ddb1d3c4`，远端 `py_compile` 通过。
- 最新 live refresh 显示 `ros2_available=true`、`ros2_cli_check.ok=true`，旧 `ros2_command_unavailable` 已解除；剩余 blocker 是没有 `/scan`、`/lidar/raw_packet` 和 `base_link -> laser_frame` TF。

### Hardware Infra Engineer

- 读取 vendor 来源并通过 SSH 只读 GET `health`、`radar/status`、`radar/scan-proof/latest`、`base/status`。
- 确认 `safe_to_control=false`、`robot_control_executed=false`、`hil_pass=false`。
- 确认历史 scan proof 不是本次 fresh refresh；`T=1001` 只能作为 vendor feedback material，不是 robot ACK。
- 未改文件，未执行任何底盘运动或 HIL。

### Full-Stack Software Engineer

- `pc-tools/workstation/src/shared/contracts.ts`：direct-upper command response 增加 `upper_result_summary`。
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`：提取 upper `status`、proof status、artifact、freshness、blockers、not_proven 和固定安全字段；HTTP 2xx 但 upper not_proven 时保持 fail-closed。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`：Refresh scan proof 结果展示 upper not_proven 和 blockers。
- `pc-tools/workstation/test/App.test.ts`：覆盖 HTTP 200 + `ros2_command_unavailable` / `upper_api_scan_not_proven` 的 API/UI 回归。
- `docs/interfaces/o7_direct_upper_pc_api.md`、`docs/product/pc_tools_workstation.md`：同步 O7 不涨分边界。
- 未做 live smoke，O7 不涨分。

## 验证结果

### Robot Software

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
```

```text
Ran 28 tests in 1.966s
OK (skipped=2)
```

```bash
python3 -m compileall -q onboard/scripts
```

```text
passed with no output
```

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/o7_upper_robot_api.md docs/interfaces/lidar_ros2_closed_loop.md sprints/2026.06.04_22-23_runtime-material-deploy-refresh/owner_notes/robot-software-engineer.md
```

```text
passed with no output
```

Live endpoint:

```text
GET /health -> HTTP 200, status=ready, safe_to_control=false
GET /api/radar/status -> HTTP 200, controls.scan_proof_refresh.endpoint=/api/radar/scan-proof/refresh, scan_status=not_proven
POST /api/radar/scan-proof/refresh -> HTTP 200, status=refreshed, proof_state=blocked_or_not_observed
GET /api/radar/scan-proof/latest -> HTTP 200, artifact_status=loaded, proof_status=blocked_or_not_observed
ros2_available=true, ros2_cli_check.ok=true
blocker=upper_api_scan_not_proven
topic details: /scan not published, /lidar/raw_packet not published, base_link -> laser_frame TF absent
```

### Hardware

```text
SSH read-only GET health/radar/status/latest/base/status passed.
safe_to_control=false
robot_control_executed=false
hil_pass=false
T=1001 remains vendor_feedback_material, not robot ACK.
No base/manual, /cmd_vel, T=1/T=13/T=130/T=131, HIL or motion command executed.
```

```bash
git diff --check -- docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/hardware/o1_pc_manual_lidar_hil_boundary.md docs/interfaces/lidar_ros2_closed_loop.md
```

```text
passed with no output
```

### Full-Stack

```bash
cd pc-tools/workstation && npm test -- --run
```

```text
Test Files 3 passed (3)
Tests 101 passed (101)
```

```bash
cd pc-tools/workstation && npm run build
```

```text
passed
```

```bash
cd pc-tools/workstation && npm run lint
```

```text
passed
```

```bash
git diff --check -- pc-tools/workstation docs/interfaces/o7_direct_upper_pc_api.md docs/product/pc_tools_workstation.md
```

```text
passed with no output
```

## 偏差和失败定位

- 已完成：部署 blocker 解除，live refresh route 不再 HTTP 405。
- 已完成：systemd ROS logging environment blocker 解除，collector 不再因为 `Failed to get logging directory` 遮蔽真实 topic 状态。
- 未完成：fresh `/scan` runtime proof 未成立。
- 当前 root cause：
  - `upper_api_scan_not_proven`: 8787 radar status 仍为 `not_proven`。
  - `/scan`、`/lidar/raw_packet` 和 `base_link -> laser_frame` TF 未发布；本轮 collector 合同只读 existing topics，不启动 driver。
- Product 判定：本轮是 `blocked_with_root_cause + deployment_progress + software_guard`，不是 O3/O7 `robot_runtime_material` 完成。

## OKR 影响

| Objective | 本轮变化 | 判定 |
| --- | --- | --- |
| O3 | 不涨分 | 解除 405 但没有 fresh `/scan`、hz、raw packet、TF、map、AMCL 或 Nav2 material。 |
| O7 | 不涨分 | PC 展示 fail-closed blockers，但未做 live smoke，也没有 fresh operator runtime workflow。 |
| O8 | 约 43% -> 约 44% | Epic 留档完成，部署 405 blocker 解除，root cause 收敛到 ROS2 command unavailable，PC blocker display 补齐。 |
| O1/O2/O5/O6 | 不变 | 本轮不触达 HIL、电梯图片、production cloud 或 archive runtime。 |

## 剩余风险

- 上位机 ROS2 CLI/logging environment 已修复，但 LiDAR ROS2 driver 或对应 topic/TF runtime 仍未启动或未发布。
- 未证明 fresh `/scan` once/hz、`/lidar/raw_packet`、TF、SLAM `/map`、AMCL、Nav2 lifecycle 或固定路线。
- 未证明 PC WASD、底盘 HIL、robot ACK、`safe_to_control=true` 或 delivery success。
- O2 真实/受控电梯图片 manifest 仍缺。

## Direct-upper 安全边界 follow-up

### 实际改动

- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`：将 direct-upper base URL 选择从 boolean 改成显式策略名，避免底盘相关入口误读 `true/false` 后意外走 field default。
- 最终安全边界保持：`status`、`radar start/stop`、`scan-proof refresh`、`operator-report` 缺 env 可使用现场 field default；`base/stop`、`base/feedback-request`、`base/manual`、`map/*`、`localize/reset` 缺 env 必须 fail-closed。
- 未改 UI 功能，未触发 live upper，未执行底盘运动。

### 验证结果

```bash
cd pc-tools/workstation && npm test -- --run
```

```text
Test Files 3 passed (3)
Tests 101 passed (101)
```

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check -- pc-tools/workstation docs/interfaces/o7_direct_upper_pc_api.md docs/product/pc_tools_workstation.md sprints/2026.06.04_22-23_runtime-material-deploy-refresh/owner_notes/full-stack-software-engineer.md
```

```text
all passed
```

### 剩余风险

- 本 follow-up 不发送真实 `/api/base/manual` forward live curl，不执行底盘运动，不证明 HIL、robot ACK、`T=1001` 或 `safe_to_control=true`。
- 现场 PC 若要启用底盘 stop/manual/feedback-request，仍必须显式配置 `ROBER_UPPER_API_BASE_URL` 或使用 fixture；缺 env 自动 fail-closed 是保留安全边界。
