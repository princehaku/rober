# 2026-06-21 23:50 Plain First Jog Control

## sprint_type

micro

## 功能设计

目标：继续推进“能移动、能在 PC 上连接和控制”，把上一轮后端
`/api/robot-control/base/first-jog` 接到普通 PC 首屏，但不把工程控制台风格带回首屏。

普通用户流程：

1. 在 `移动/导航` 卡片输入“现场画面记录”，例如手机视频编号或文件名。
2. 点击 `记录画面`，PC 通过既有固定 `/api/robot-control/operator/report` 代理提交：
   - `operator_present=true`
   - `physical_clearance_confirmed=true`
   - `emergency_stop_ready=true`
   - `external_video_recorded=true`
   - `external_video_ref=<用户输入>`
   - wheel feedback、LiDAR delta、route map、delivery success 仍为 false。
3. 点击 `试动一下`，PC 调用固定
   `POST /api/robot-control/base/first-jog?baseUrl=<robot-api-base-url>`，请求固定为
   `forward speed=0.08 duration_ms=500 confirm_hil_checklist=true`。
4. 如果后端 first-jog preflight 缺材料，普通首屏只显示“还需要先记录现场画面，小车没有移动”。
5. 如果后端成功转发，普通首屏只显示“试动请求已发送”，不能宣称 HIL pass、delivery success 或真实运动成功。

边界：

- 普通首屏仍保持 `Rober 小车控制台` + `.simple-user-console` 五卡片。
- 不显示 `HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`task_id`、`O6/O7` 等工程词。
- 不开放方向键、连续控制、速度输入、时长输入、地图点击目标或任意 endpoint。
- first-jog 后端仍是最终安全门；前端记录画面只是人工材料提交，不证明画面真实有效。

## 实际改动

- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `postRobotControlBaseFirstJog`，只调用固定
    `/api/robot-control/base/first-jog?baseUrl=...`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `移动/导航` 卡片新增 `现场画面记录` 输入框、`记录画面` 和 `试动一下`。
  - `记录画面` 提交外部视频 ref 到固定 operator report 代理，并保持 wheel feedback、LiDAR delta、route map、delivery success 为 false。
  - `试动一下` 固定调用 first-jog，body 为 `direction=forward`、`speed=0.08`、`duration_ms=500`、`confirm_hil_checklist=true`。
  - first-jog 被拒绝时普通首屏显示“小车没有移动”，不展示 `first_jog_preflight_required` 或工程字段。
- `pc-tools/workstation/src/styles.css`
  - 为普通首屏的视频记录输入补最小稳定尺寸。
- `pc-tools/workstation/test/App.test.ts`
  - 新增普通视频记录 + first-jog UI 回归，确认不调用旧 manual 前端代理、不伪造轮速/LiDAR。
- `docs/product/pc_tools_workstation.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/hardware/board_sensor_stack_smoke.md`
  - 同步普通 first-jog 控制入口、安全边界和真实 smoke 结果。
- `sprints/2026.06.21_23-50_plain_first_jog_control/artifacts/`
  - 记录当前真实板端缺可视材料时的 first-jog reject 请求、响应、HTTP 状态和 summary。

## 验证结果

已完成：

- `cd pc-tools/workstation && npm run test -- App.test.ts`
  - 结果：通过，`19` 个测试通过。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过。
- 真实 PC proxy no-motion reject smoke：
  - 本机 workstation API：`http://127.0.0.1:18822`
  - 真实上位机：`http://192.168.1.11:8787`
  - 请求：`POST /api/robot-control/base/first-jog?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - 请求体：`direction=forward`、`speed=0.08`、`duration_ms=500`、`confirm_hil_checklist=true`
  - 结果：HTTP `400`、`proxy_status=command_rejected`、`failure_reason=first_jog_preflight_required`
  - `remote_http_status=null`、`robot_control_executed=false`
  - 缺项：`external_video_or_visible_camera`
  - 结论：当前真实 operator report 仍缺可视材料，PC first-jog 入口没有调用远端 `/api/base/manual`。

收口验证：

- `cd pc-tools/workstation && npm run test`
  - 结果：通过，`2` 个测试文件、`98` 个测试通过。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`
  - 结果：通过，无 whitespace error。
- artifact JSON parse：
  - `01_first_jog_ui_reject_request.json`、`02_first_jog_ui_reject_response.json`、`03_summary_after_ui_reject.json` 均可解析。
- 上位机只读清场：
  - `trashbot-upper-robot-api.service=active`
  - `trashbot-local-webrtc-camera.service=active`
  - `pgrep -af "o10_amcl_nav2_runtime_proof|nav2|amcl|map_server"` 只匹配本次检查命令本身。
  - `fuser /dev/ttyS5 /dev/ttyACM0` 无输出，未发现本轮遗留占用。

## 剩余风险

- 当前仍没有真实移动证据；本轮只是把 first-jog 接到普通 PC 控制入口，并证明缺材料时不会发车。
- 如现场人员在普通首屏填写外部视频 ref，后端 first-jog 会按当前安全策略允许首次低速试动；这依赖人工材料真实性。
- 地图仍存在 `free=0` / `navigation_quality=no_free_cells` 风险，不能进入 Nav2/fixed-route movement。
- 相机 first-frame / 可见内容链路仍未稳定证明。
