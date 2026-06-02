# 2026.06.02 20-21 O7 Camera Offer Recovery Tech Done

## Sprint 类型

- sprint_type: micro
- Owner: Product Manager / OKR Owner closeout；实现与验证证据来自 Hardware 只读诊断、Full-Stack 修复与 verification worker。
- 本轮文件边界：只更新 `OKR.md`、`docs/process/okr_progress_log.md`、本文件；不改产品代码、测试或硬件配置。

## 用户价值和产品北极星

北极星仍是普通手机用户可理解、可操作、可诊断的低成本自主垃圾投递机器人。O7 的用户价值不是“又多一个 smoke”，而是让 PC 运营调试平台能稳定看到同 LAN 真实摄像头视频材料，并把 camera source 错选这类板端环境问题变成可防护、可复验、可继续生产化的证据链。

## OKR 映射和方向判断

- O1：保持约 93%，方向为继续但本轮暂停消费当前 blocker。`target_port_identity_possible_lidar_or_other_stc_before_more_T130` 需要现场物理拔插/追线确认，不能继续盲发 `T=130`。
- O5：保持约 96%，方向为继续；本轮未推进真实生产云、公网 HTTPS、4G/SIM、production DB/queue 或 OSS/CDN live traffic。
- O6：保持约 96%，方向为继续；本轮未推进真实隧道、production archive、真实 OSS upload、模型推理 runtime 或上车数据。
- O7：从约 96% `blocked real-material failure classification` 上调为约 97% `same-LAN 180s real browser material accepted + camera source guardrail ready`，方向为继续。

## 本轮核心抓手

上一轮 O7 blocker 是 `camera_service_ready_but_first_frame_timeout_offer_http_500`。本轮证据把根因收敛为 camera source 错选：`ROBER_CAMERA_SOURCE=0` 命中 `/dev/video0` cedrus platform Video Memory-to-Memory codec，不是 capture 摄像头；真实 USB camera 是 `/dev/video1`，driver `uvcvideo`，`Video Capture`，OpenCV `VideoCapture('/dev/video1', CAP_V4L2)` 可打开并读取 640x480。`/dev/video2` 是 metadata 节点。未发现占用、权限或 Python import 问题。

Full-Stack 改动事实：`local_webrtc_camera_smoke.py` 默认 source 改为 `auto`，auto 逐个 `/dev/video*` 通过 V4L2 打开并读取首帧，跳过不可读节点；shell 默认 `ROBER_CAMERA_SOURCE=auto`；测试覆盖 auto 跳过 `/dev/video0` 选择 `/dev/video1`；相关 docs 已同步。

## 实际改动

- `OKR.md`：更新 O7 当前进度、4.1 快照、最高优先级排序和 O7 MVP 路线；O7 上调到约 97%，同时保留生产路径未证明边界。
- `docs/process/okr_progress_log.md`：新增 `2026-06-02 20-21｜o7-camera-offer-recovery` 历史记录。
- `sprints/2026.06.02_20-21_o7-camera-offer-recovery/tech-done.md`：创建本轮 Micro sprint 收口记录。

## 验收证据

远端部署/重启后：

- `/health status=ready video_source=/dev/video1 active_peer_connections=0`
- 30s browser smoke：`status=ok offer_http_status=200 first_frame_received=true video_width=640 video_height=480 first_frame_ms=2315 estimated_fps=13.93 server_peer_close_status=200:closed post_close_active_peer_connections=0`
- 180s long-stability：`status=ok observation_window_ms=180000 first_frame_received=true first_frame_ms=1928 estimated_fps=13.92 framesDecoded=2507 console_errors_added=0 page_errors_added=0 post_close_active_peer_connections=0`

本地 verification worker 证据：

- `py_compile` passed
- unittest：`Ran 7 tests ... OK`
- `npm run o7:camera-service-readiness -- --dry-run` passed，且无 network/ssh/post/webrtc/artifact flags
- `npm run test`：2 files / 63 tests
- `npm run build`：35 modules transformed / built
- `npm run lint` passed
- scoped diff-check passed

本轮 Product 文档验收命令：

- 已通过：`git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.02_20-21_o7-camera-offer-recovery/tech-done.md`

## 优先级和验收口径

P0：O7 camera source guardrail 与 same-LAN 180s browser material 接受。验收口径是 180s browser collector `status=ok`、首帧收到、640x480、稳定窗口 180000ms、无新增 console/page errors、peer close 后 active connections 回到 0。

P1：继续补 production path。验收口径不能用 same-LAN 180s 替代，必须另采 cloud relay/TURN/auth/phone/browser、systemd persistence 和弱网材料。

P2：O1 仍是最低 Objective，但下一步必须现场物理拔插/追线。验收口径是对比 LiDAR 与 WAVE ROVER ESP32/底盘控制器插拔后的 by-id/by-path/`/dev/lidar`/realpath 变化，再决定是否运行 vendor terminal `T=130` 交叉验证。

## 对应责任 Engineer

- Hardware Infra Engineer：只读确认 camera source root cause，并继续负责 O1 现场物理追线/插拔证据。
- User Touchpoint Full-Stack Engineer：负责 O7 local WebRTC camera smoke、browser collector、PC workstation 验收队列和相关 docs。
- Robot Software Engineer：本轮无代码责任；后续如果 video path 要接 ROS2/robot status，再负责接口 glue。
- Robot Algorithm Engineer：本轮无代码责任；后续若 camera material 接入视觉/标注训练闭环，再负责算法侧验收。

## 风险、阻塞和证据链缺口

- O7 只证明 same-LAN 真实浏览器 180s 材料接受，不证明 cloud relay、TURN、auth、phone/browser production path。
- camera smoke service 仍缺 systemd persistence 证据，operator-run/nohup 不等于生产守护。
- 弱网、长时间超过 3-5 分钟、手机浏览器差异、断连恢复、权限轮转仍未证明。
- ASR/TTS、手控/Nav2、robot ACK、完整 onboard task 和真实垃圾投递闭环仍 `not_proven`。
- O1 当前 blocker 仍要求现场物理拔插/追线；本轮没有触碰 WAVE ROVER、serial、`T=130/T=1/T=13/T=131`、`cmd_vel`、ROS2/Nav2 或 robot control。

## KR 历史归档判断

本轮没有已完成 KR 移入历史归档区。O7 的“同 LAN 180s 真实浏览器材料”是当前推进区的重要完成证据，但 PC 端运营调试平台的生产路径、手机/公网、系统守护和完整上车任务仍未完成，因此不归档 O7 KR。

历史记录位置：

- `docs/process/okr_progress_log.md`：`2026-06-02 20-21｜o7-camera-offer-recovery`
- `OKR.md`：Objective 7、4.1 当前 OKR 进度快照、当前最高优先级、O7 MVP 路线
- 本文件：`sprints/2026.06.02_20-21_o7-camera-offer-recovery/tech-done.md`

## 文档同步和工程质量监管

- docs 同步：本轮 Product closeout 已更新 `docs/process/okr_progress_log.md`；Full-Stack 证据显示相关产品/接口 docs 已在实现轮同步。
- 代码注释监管：本轮 Product 不修改代码。根据 verification worker 安全边界，本轮 closeout 不新增技术代码注释风险；后续代码变更仍必须保持中文技术注释比例超过 20%。
