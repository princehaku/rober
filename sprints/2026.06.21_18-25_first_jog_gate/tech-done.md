# 2026-06-21 18:25 First Jog Gate

## sprint_type

micro

## 功能设计

目标：推进“能移动、能在 PC 上控制”，但不绕过安全边界。现有非 stop manual gate 要求
`wheel_feedback_lr_nonzero_proven` 和 `physical_motion_lidar_delta_proven` 作为前置材料；
这两个材料本质上需要第一次真实低速动作后才能产生，形成循环。本轮新增一个“首次低速试动”
固定代理来打破循环。

新增 PC 后端固定代理：

```text
POST /api/robot-control/base/first-jog?baseUrl=<robot-api-base-url>
```

设计边界：

- 只允许 `forward/back/left/right`，不接受 `stop`；停车仍用既有 `/api/robot-control/base/stop`。
- 仍 clamp `speed <= 0.12m/s`、`duration <= 800ms`。
- 必须 `confirm_hil_checklist=true`。
- 必须读取上位机固定 `GET /api/operator/report` 做 first-jog preflight。
- first-jog preflight 前置只要求：
  - `operator_present=true`
  - `physical_clearance_confirmed=true`
  - `emergency_stop_ready=true`
  - 且满足下列任一可视材料：
    - `external_video_recorded=true` 且 `external_video_ref` 非空；
    - 或 `visible_content_proven=true` 且 `camera_artifacts_ref` 非空。
- 不要求 `wheel_feedback_lr_nonzero_proven` 或 `physical_motion_lidar_delta_proven` 作为前置；它们是本次试动后的输出证据。
- 通过后才转发到上位机固定 `/api/base/manual`。响应仍固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，不能把一次试动解释成 HIL pass 或交付成功。
- 当前真实上位机 operator report 仍缺 external video 和 visible camera，因此真实 smoke 预期应拒绝，不应调用远端 `/api/base/manual`。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 first-jog 专用 operator report preflight。
  - first-jog 前置只要求 operator 基础三项和 `external_video_or_visible_camera`，不再把 wheel feedback 与 LiDAR delta 当作首次试动前置。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 `POST /api/robot-control/base/first-jog?baseUrl=<robot-api-base-url>`。
  - 该入口只允许 `forward/back/left/right`，clamp `speed<=0.12`、`duration_ms<=800`，要求 `confirm_hil_checklist=true`。
  - preflight 未通过时本机 HTTP 400 拒绝，不调用远端 `/api/base/manual`。
  - preflight 通过后只转发一次固定 `/api/base/manual`，响应顶层仍保持 fail-closed。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 把 first-jog 固定代理加入 API route 清单。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 first-jog 缺可视材料拒绝用例。
  - 新增 first-jog 有可视材料时只转发一次 clamp 后 fixed `/api/base/manual` 的用例。
- `docs/product/pc_tools_workstation.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/hardware/board_sensor_stack_smoke.md`
  - 同步记录 first-jog 的安全边界、真实 smoke 结果和剩余缺口。
- `sprints/2026.06.21_18-25_first_jog_gate/artifacts/`
  - 记录真实 PC proxy first-jog reject 请求、响应、HTTP 状态和 reject 后 summary。

## 验证结果

已完成：

- `cd pc-tools/workstation && npm run test -- catalog.test.ts`
  - 结果：通过，`79` 个测试通过。
- 真实 PC proxy smoke：
  - 本机 workstation API：`http://127.0.0.1:18821`
  - 真实上位机：`http://192.168.1.11:8787`
  - 请求：`POST /api/robot-control/base/first-jog?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - 请求体：`direction=forward`、`speed=0.08`、`duration_ms=500`、`confirm_hil_checklist=true`
  - 结果：HTTP `400`、`proxy_status=command_rejected`、`failure_reason=first_jog_preflight_required`
  - `remote_http_status=null`、`robot_control_executed=false`
  - `operator_report_preflight.missing_fields=["external_video_or_visible_camera"]`
  - 结论：当前真实上位机缺外部视频或可见相机 ref，first-jog 正常拒绝，未调用远端 `/api/base/manual`。

收口验证：

- `cd pc-tools/workstation && npm run test`
  - 结果：通过，`2` 个测试文件、`97` 个测试通过。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过。
- `git diff --check`
  - 结果：通过，无 whitespace error。
- artifact JSON parse：
  - `01_first_jog_reject_request.json`、`02_pc_first_jog_reject_response.json`、`03_pc_summary_after_first_jog_reject.json` 均可解析。
- 上位机只读清场：
  - `trashbot-upper-robot-api.service=active`
  - `trashbot-local-webrtc-camera.service=active`
  - `pgrep -af "o10_amcl_nav2_runtime_proof|nav2|amcl|map_server"` 只匹配本次检查命令本身。
  - `fuser /dev/ttyS5 /dev/ttyACM0` 无输出，未发现本轮遗留占用。

## 剩余风险

- 当前仍没有真实移动证据；本轮只增加安全的首次试动入口，并证明真实现场材料不足时不会发送运动。
- 真实 first-jog 仍需要现场提供外部视频 ref 或可见相机 artifact ref。
- 现有地图仍存在 `free=0` / `navigation_quality=no_free_cells` 风险，不能进入 Nav2/fixed-route movement。
- 相机 first-frame / 可见内容链路仍未稳定证明，不能把图传当作可视材料默认通过。
