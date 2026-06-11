# sprint_type: micro

## 本轮目标与边界

本轮用本机 workstation Node proxy `http://127.0.0.1:18793` 连接真实上位机 Robot API
`http://192.168.1.11:8787`，完成低风险真实板端 smoke：summary 读取、radar proof refresh、
map proof refresh、Nav2 no-motion proof refresh、camera health/devices 只读 readback、
base stop smoke，以及 manual 非 stop gate rejection。

本轮严格不执行非 stop motion，不调用真实 `/api/base/manual` 成功路径，不发布 `/cmd_vel`，
不改变 PC 普通用户首屏风格。默认首屏仍必须是 `Rober 小车控制台` +
`.simple-user-console` 五卡片：`小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。

## 已读资料来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.06.11_18-20_board_live_evidence_sweep/tech-done.md`
- `sprints/2026.06.11_18-45_pc_real_board_control_smoke/tech-done.md`

硬件事实仍以 `docs/vendor/VENDOR_INDEX.md` 指向的本地资料为准：WAVE ROVER 上下位机使用
UART newline-delimited UTF-8 JSON；vendor 示例包含 `T=1` 左右轮速度、`T=13` ROS control、
`T=130` base feedback request、`T=1001` base feedback。本轮只通过 PC proxy 调用
上位机 HTTP API，不新增串口、引脚、电压、波特率或运动映射假设。

## 用户旅程变化和触点收益

- 普通用户首屏未变化，继续保留简易五卡片视图，不把工程 proof、HIL、Nav2、`/cmd_vel`
  或 `/api/base/manual` 放回默认可见区。
- 运维/调试人员现在有一组 artifacts 证明 PC 层 Node proxy 能连到真实上位机，并能通过固定
  proxy endpoint 执行只读或 fail-safe smoke。
- 非 stop manual 请求在现场 HIL 材料不足时被 workstation 本机 HTTP 400 拒绝，用户不会误以为
  PC 已经开放真实点动控制。

## 实际改动

- 新增本轮 sprint 留档：
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/tech-done.md`
- 新增 artifacts：
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/summary.json`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/radar_refresh.json`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/map_refresh.json`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/nav2_refresh.json`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/post_summary.json`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/camera_health_devices_from_summary.json`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/base_stop.json`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/manual_non_stop_gate_rejection.json`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/pc_proxy_smoke_key_conclusions.json`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/logs/http_codes.log`
  - `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/logs/cleanup.log`
- 同步更新：
  - `docs/product/pc_tools_workstation.md`
  - `pc-tools/README.md`
- 未改：
  - `pc-tools/workstation/src/App.vue`
  - `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `pc-tools/workstation/src/styles.css`
  - `pc-tools/workstation/test/App.test.ts`
  - onboard 硬件、driver、launch 配置

## 真实上位机 PC proxy smoke 结果

临时 workstation API：`http://127.0.0.1:18793`。

真实上位机 Robot API：`http://192.168.1.11:8787`。

HTTP code：

```text
summary_http=200
radar_refresh_http=200
map_refresh_http=200
nav2_refresh_http=200
post_summary_http=200
base_stop_http=200
manual_non_stop_gate_rejection_http=400
```

关键 readback：

- Summary：PC proxy 可访问真实上位机，顶层保持 `safe_to_control=false`、
  `delivery_success=false`、`primary_actions_enabled=false`。summary 聚合命中
  `base.feedback_readback.sends_commands` / `base.sends_commands` 危险 true 字段后保持
  fail-closed blocked；这不放行控制。
- Camera：从 summary 的 `read_endpoints` 只读到 `camera_health` 与 `camera_devices`；
  `readback_summary.camera.status=ready`、`devices_status=loaded`、`preview_status=idle_not_started`。
  本轮未打开 camera offer peer，因此无需 close cleanup。
- Radar refresh：`proxy_status=refresh_forwarded`、`remote_http_status=200`、
  `remote_endpoint=/api/radar/scan-proof/refresh`、`evidence_ref=o1-lidar-scan-proof-1781172841393`。
  最新 key values 显示 `scan_once_observed=true`、`scan_hz_observed=true`、
  `raw_packet_once_observed=true`、`tf_observed=true`，但 `lifecycle_running=false`、
  `continuous_window_observed=false`、`latest_scan_proof_fresh=false`。
- Map refresh：`proxy_status=refresh_forwarded`、`remote_http_status=200`、
  `remote_endpoint=/api/map/proof/refresh`、`evidence_ref=o3-map-lifecycle-1781172868360`，
  `map_once_observed=true`、`map_file_observed=true`、`map_metadata_observed=true`。
- Nav2 refresh：`proxy_status=refresh_forwarded`、`remote_http_status=200`、
  `remote_endpoint=/api/nav2/proof/refresh`、
  `evidence_ref=o10-amcl-nav2-runtime-wrapper-failure-1781172997846`。
  远端执行的是 no-motion proof refresh，但结果为 `status=blocked_with_root_cause`、
  `managed_runtime_started=true`、`initialpose_published=true`、`path_generation_requested=true`、
  `path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`、
  `planner_server_active=false`。这证明 proxy 请求链路可达，但不证明 Nav2 path ready。
- Base stop：`proxy_status=command_forwarded`、`remote_http_status=200`、
  `remote_endpoint=/api/base/stop`、`status=stopped`，`evidence_capture_status=captured`。
  响应顶层仍固定 `robot_control_executed=false`、`safe_to_control=false`、
  `delivery_success=false`。
- Manual non-stop gate：`forward speed=0.12 duration_ms=800 confirm_hil_checklist=true`
  被本机 proxy HTTP 400 拒绝，`proxy_status=command_rejected`、`remote_http_status=null`、
  `failure_reason=operator_report_preflight_required`。缺失项为
  `external_video_recorded`、`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`、
  `physical_motion_lidar_delta_proven`。未调用真实 `/api/base/manual` 成功路径。

## 验证结果

运行时间：2026-06-11 18:17-18:18 CST。

### `cd pc-tools/workstation && npm run test`

通过。

```text
Test Files  2 passed (2)
Tests  92 passed (92)
Duration  8.52s
```

### `cd pc-tools/workstation && npm run build`

通过。

```text
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 2.49s
```

### PC Node proxy 到真实上位机 smoke

通过并产生 artifacts。覆盖 summary、radar refresh、map refresh、Nav2 no-motion refresh、
camera health/devices readback、base stop、manual non-stop gate rejection。

```text
summary_http=200
radar_refresh_http=200
map_refresh_http=200
nav2_refresh_http=200
base_stop_http=200
manual_non_stop_gate_rejection_http=400
```

### `git diff --check`

通过。

```text
git diff --check -- sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke docs/product/pc_tools_workstation.md pc-tools/README.md pc-tools/workstation/test/App.test.ts
```

无输出。

### 端口清理

临时 API 已停止。清理检查：

```text
lsof -nP -iTCP:18793 -sTCP:LISTEN
```

无输出，`cleanup.log` 记录 `lsof_exit_code=1`。

## 失败定位

- Nav2 no-motion refresh 的 PC proxy 链路成功，但真实上位机 proof 结果为
  `blocked_with_root_cause`，未生成 path，planner server 未 active。本轮将其记录为真实
  Nav2 proof gap，不把它解释成导航可用。
- Summary 聚合中 base readback 暴露 `sends_commands=true` 字段，被 workstation 危险字段扫描
  标记为 blocked；这是 fail-closed 行为，不影响固定 stop smoke，但说明 summary 不能被用作
  控制放行依据。
- Manual 非 stop 被拒绝是预期安全结果：operator report 仍缺外部视频、相机可见内容、轮速非零反馈
  和 LiDAR delta 物理运动材料。

## 剩余风险

- 本轮只证明 PC workstation proxy 到真实上位机的 HTTP 合同和安全 gate，不证明真实点动、真实路线执行、
  Nav2 规划可用、HIL pass、delivery success 或普通用户可控制。
- Camera 本轮只读 health/devices，未打开 WebRTC offer，也未证明画面内容可见。
- Radar refresh 有一次性 scan/raw/tf 证据，但 lifecycle stopped、continuous window 未证明。
- Nav2 path generation 本轮失败，需 robot/algorithm 侧继续定位 managed runtime / planner root cause。
- stop smoke 写入成功不等于物理停车视频证明；仍需真实 HIL 材料补齐。

## 完成前反思

- 需求满足：已通过 PC Node proxy 连接真实上位机并覆盖要求的 summary、refresh、camera readback、
  stop 和 manual gate rejection。
- 范围控制：未修改普通用户首屏 UI、样式或测试断言，未改 onboard 硬件/driver/launch 配置。
- 验证缺口：Nav2 no-motion path generation 未通过；camera 可见内容与真实非 stop motion 仍未验证。
- 文档同步：已把本轮 PC proxy real-board smoke 证据边界追加到 `docs/product/pc_tools_workstation.md`
  与 `pc-tools/README.md`。
