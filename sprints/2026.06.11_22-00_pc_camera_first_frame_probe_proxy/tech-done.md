# PC Camera First-frame Probe Proxy

## sprint_type

micro

## 背景

继续推进“PC 页面完整控制小车雷达、建图、定位移动、手动移动、实时图传”的真实上车目标。
上一轮已经把相机首帧探针入仓并证明 `/dev/video1` 底层 `open_ok=true/read_ok=false`。
本轮按用户要求不再调用 subagent，直接把该探针接入上位机 API 与 PC 高级诊断，让 PC 页面
可以一键触发同一条真实板端 first-frame probe。

本轮硬件资料入口：

- `docs/vendor/VENDOR_INDEX.md`

本轮不调用 `/api/base/manual`，不发布 `/cmd_vel`，不执行 Nav2 goal，不打开
WAVE ROVER UART，不触碰 `/dev/ttyS5`。

## 设计

- 上位机新增固定 endpoint：
  - `POST /api/camera/first-frame/probe`
  - 内部只调用 `onboard/scripts/camera_first_frame_probe.py`
  - HTTP body 只接受短白名单参数；PC 默认空 body，由上位机固定为 `/dev/video1 + MJPG + 640x480`
- PC Node 新增固定代理：
  - `POST /api/robot-control/camera/first-frame/probe?baseUrl=...`
  - 只转发到上位机固定 endpoint，不允许浏览器传任意设备、shell 参数或 URL path
  - timeout 单独设为 12s，避免 4s read guard 加进程开销被 PC wrapper 误杀
- Vue 高级诊断新增按钮：
  - “首帧探针（高级）”
  - 普通用户首屏不展示该工程诊断入口
  - 展示 open/read/timeout/failure/luma 短字段，不透传整份远端 JSON

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `camera_first_frame_probe` route path；
  - 新增 `safe_camera_probe_request`、`run_camera_first_frame_probe`；
  - 新增 aiohttp handler 并挂载 `POST /api/camera/first-frame/probe`。
- `onboard/tests/test_upper_robot_api.py`
  - 新增参数白名单、缺脚本 fail-closed、subprocess JSON 解析测试。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlCameraFirstFrameProbeProxyResponse`。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `postRobotControlCameraFirstFrameProbe`。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 PC camera first-frame probe 固定代理；
  - 新增短 key-values 摘要和 fail-closed fallback；
  - probe 使用 12s timeout，避免误杀真实 4s read guard。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 高级诊断“实时画面详情”新增首帧探针按钮和结果字段；
  - `.simple-user-console` 普通首屏未改。
- 新增 artifacts：
  - `artifacts/01_local_hashes.txt`
  - `artifacts/02_remote_deploy_restart.txt`
  - `artifacts/03_remote_first_frame_probe.txt`
  - `artifacts/04_pc_proxy_first_frame_probe.json`
  - `artifacts/05_pc_proxy_summary_after_probe.json`
  - `artifacts/06_remote_cleanup.txt`

## 验证结果

本地验证：

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/camera_first_frame_probe.py
python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_camera_first_frame_probe
python3 -m unittest discover onboard/tests
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
git diff --check
```

结果：

- `test_upper_robot_api + test_camera_first_frame_probe`：35 tests OK
- `onboard/tests`：106 tests OK
- PC workstation：92 tests passed
- PC workstation build：通过
- `git diff --check`：通过

上板部署：

- 远端 `upper_robot_api.py` hash：
  - `fe0b3972ef1c67ab976fae03b81699fde0521ea32ea07abd998fc876ecf86f67`
- 远端 `camera_first_frame_probe.py` hash：
  - `f9fd64e4c6571f0b5f2ed68f64ce3fbe3dc41d20a77b4dcd77d7528a5bc2f1b7`
- `trashbot-upper-robot-api.service=active`

真实上位机 direct probe：

- `POST http://127.0.0.1:8787/api/camera/first-frame/probe`
- `status=first_frame_timeout`
- `probe_request.device=/dev/video1`
- `probe_request.fourcc=MJPG`
- `probe_payload.open_ok=true`
- `probe_payload.read_ok=false`
- `probe_payload.failure_reason=capture_read_call_timeout`
- `probe_payload.visible_content_proven=false`
- `safe_to_control=false`
- `robot_control_executed=false`

真实 PC proxy probe：

- `POST http://127.0.0.1:18807/api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787`
- `remote_http_status=503`
- `status=first_frame_timeout`
- `probe_key_values.device=/dev/video1`
- `probe_key_values.requested_fourcc=MJPG`
- `probe_key_values.open_ok=true`
- `probe_key_values.read_ok=false`
- `probe_key_values.first_frame_timeout=true`
- `probe_key_values.failure_reason=capture_read_call_timeout`
- `probe_key_values.visible_content_proven=false`
- `hard_dangerous_true_fields=[]`
- `robot_control_executed=false`

收尾状态：

- `trashbot-upper-robot-api.service=active`
- `trashbot-local-webrtc-camera.service=active`
- `/api/camera/health status=ready`
- `/api/camera/health video_source=/dev/video1`
- `/api/camera/health active_peer_count=0`
- `fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5` 无残留 holder 输出

## 剩余风险

- 这轮完成的是 PC 到上位机到底层 camera first-frame probe 的诊断闭环，不是相机恢复。
- 真实 `/dev/video1` 仍然 `open_ok=true/read_ok=false`，首帧不可读。
- PC 实时图传可见内容仍未恢复，仍需现场确认 DV20 输入源、线缆、供电、采集卡状态，
  或插入 known-good UVC 后用 PC 高级诊断按钮复测。
- 运动 HIL gate 仍缺 `visible_content_proven=true`、外部视频、轮速反馈非零和 LiDAR
  motion delta，不能放行非 stop 运动。
