# PC Base Feedback Samples Proxy

## sprint_type

micro

## 目标

在不调用 subagent、不发送运动命令的前提下，让 PC 页面可以从默认关闭的高级诊断里主动采集一次真实 WAVE ROVER 只读反馈样本，为后续手动点动 gate 补齐底盘反馈链路证据。

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/hardware/wave_rover_json_bridge.md`

采用事实：WAVE ROVER 上下位机链路为 UART newline-delimited JSON；vendor `T=130` 是底盘反馈请求，反馈帧为 `T=1001`；项目上车串口由现场上位机 API 持有，PC 只通过固定 HTTP 代理请求，不直接操作串口。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlBaseFeedbackSamplesProxyResponse` 合同。
  - 顶层安全字段保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- `pc-tools/workstation/src/server/index.ts`
  - 新增固定 `POST /api/robot-control/base/feedback-samples?baseUrl=...` 代理。
  - 代理只向上位机 `/api/base/feedback-samples` 发送后端写死短批量参数：`sample_count=3`、`sample_interval_s=0.15`、`read_timeout_s=0.25`、`read_window_s=0.35`。
  - 不接受浏览器 body 中的串口、方向、速度、duration 或 endpoint。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `postRobotControlBaseFeedbackSamples` client wrapper。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在默认关闭的高级诊断 `现场点动设置 / 控制边界` 中新增 `采集底盘反馈（高级）`。
  - 一键证据巡检在 stop 前增加一次只读底盘反馈采样。
  - 普通 `.simple-user-console` 首屏未新增工程按钮或工程字段。
- `docs/product/pc_tools_workstation.md`
  - 记录新 PC 代理边界、UI 位置和实测结果。
- `docs/hardware/wave_rover_json_bridge.md`
  - 记录 2026-06-12 真实上位机 `T=130/T=1001` 只读采样证据。

## 真实上位机验证

上位机：`root@192.168.1.11:37878`

Direct upper API：

- 命令：`POST http://192.168.1.11:8787/api/base/feedback-samples`
- artifact：`sprints/2026.06.12_02-00_pc_base_feedback_samples_proxy/artifacts/01_upper_base_feedback_samples.json`
- 结果摘要：
  - `schema=trashbot.upper_robot_api.v1.base_feedback_samples_result`
  - `requested_sample_count=3`
  - `completed_sample_count=3`
  - `t1001_observed_count=3`
  - `feedback_ack.t1001_observed=true`
  - `observed_feedback_types=[1001]`
  - `sends_motion_commands=false`
  - `robot_control_executed=false`

PC proxy：

- 本机临时 API：`PORT=18813 npm run api`
- 命令：`POST http://127.0.0.1:18813/api/robot-control/base/feedback-samples?baseUrl=http://192.168.1.11:8787`
- artifact：`sprints/2026.06.12_02-00_pc_base_feedback_samples_proxy/artifacts/02_pc_proxy_base_feedback_samples.json`
- 结果摘要：
  - `proxy_status=samples_forwarded`
  - `remote_http_status=200`
  - `status=loaded`
  - `sample_key_values.completed_sample_count=3`
  - `sample_key_values.t1001_observed_count=3`
  - `sample_key_values.feedback_ack_t1001_observed=true`
  - `sample_key_values.sends_motion_commands=false`
  - `sample_key_values.robot_control_executed=false`
  - `hard_dangerous_true_fields=[]`

收尾：

- 临时 PC API 18813 已关闭。
- `trashbot-upper-robot-api.service=active`
- `trashbot-local-webrtc-camera.service=active`
- `/dev/ttyS5`、`/dev/ttyACM0`、`/dev/video0`、`/dev/video1`、`/dev/video2` 无 holder 输出。

## 本地验证

- `npm run test -- App.test.ts`：17 passed。
- `npm run build`：通过。
- `npm run test`：93 passed。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 本轮 artifact JSON parse：通过。

## 剩余风险

- 这只证明 PC 可以主动采集真实 WAVE ROVER `T=1001` 只读反馈样本，不证明轮速非零、物理运动、方向正确或 HIL pass。
- 相机 `/dev/video1` 仍是 first-frame timeout，PC 实时可见图传未恢复。
- 非 stop 手动点动仍需要现场外部视频、可见相机、轮速非零反馈和 LiDAR motion delta 等材料后才能放行。
