# 2026.06.01 08-09 O7 Browser Stability Metrics

sprint_type: micro

## 用户价值和产品北极星

本轮把 O7 的 same-LAN Chromium 浏览器播放证据从“首帧可见”推进到“30s 短稳态可观测”：开发者和运营调试人员不仅能看到视频首帧，还能拿到浏览器 WebRTC stats、远端 `/health` 系统指标、媒体稳定性摘要和会话 cleanup 证据。产品北极星仍是普通用户只通过手机/PC 入口理解机器人状态；本轮只服务运营调试平台的视频可观测性，不把它解释成公网、手机或完整上车任务闭环已完成。

## 实际改动

- 板端 `GET /health` 新增 `system_diagnostics`、`media_stability_summary`，并补兼容扁平 `system_metrics` / `stability_metrics`，让 PC smoke 能读取远端 CPU/温度/进程内存/peer 与帧读数。
- PC browser smoke 支持 `ROBER_O7_BROWSER_SMOKE_STABILITY_MS`，首帧后继续采样 WebRTC stats 与远端 `/health`，并输出短稳态摘要。
- Product closeout 创建本 micro sprint 留档，并把 O7 OKR/progress log 从约 94% 更新到约 95%。

## 验证结果

- Robot py_compile：通过。
- Robot unittest：6 OK。
- Robot diff-check：通过。
- PC npm test：2 files / 45 OK。
- PC lint：通过。
- PC build：通过。
- PC diff-check：通过。
- 真实 30s browser smoke against `http://192.168.1.11:8088/`：通过。

关键 30s smoke 证据：

- `status=ok`
- `first_frame_received=true`
- `first_frame_ms=2044`
- `stability_summary.status=observed`
- `sample_count=6`
- `estimated_fps=13.9`
- `remote_system_metrics.process_uptime_s=370.036`
- `remote_system_metrics.load_1m=1.35009765625`
- `remote_system_metrics.process_rss_bytes=141357056`
- `remote_system_metrics.temperature_celsius=46.394`
- `remote_stability_metrics.active_peer_count=1`
- `remote_stability_metrics.active_frames_read=352`
- `remote_stability_metrics.active_camera_read_failures=0`
- `remote_active_peer_cleaned=cleaned`
- `post_close_active_peer_connections=0`
- `post_smoke_remote_health.activePeerConnections=0`
- `stabilityMetrics.last_closed_fps_estimate=13.301`
- `stabilityMetrics.last_closed_camera_read_failures=0`

## OKR 映射和方向判断

- Objective：O7 PC 端运营调试与数据训练平台。
- 方向判断：继续。
- 进度判断：O7 可从约 94% 调整到约 95%。
- 不调整 O1/O5/O6；本轮未证明 WAVE ROVER/UART/HIL、真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、live O6 API 或真实上车数据。

本轮关闭的缺口是：same-LAN Chromium 30s 短稳态 + 远端 CPU/温度/帧读数 + peer cleanup 可观测。仍不能证明 3-5 分钟稳定性、弱网、TURN、公网云 relay、鉴权、真实用户浏览器/手机、ASR/TTS、手控/Nav2、真实 robot ACK 或完整上车任务闭环。

## KR 拆解与历史归档

- KR1/实时状态可见性：增加远端 `/health` 系统与媒体稳定性观测证据，但仍未接入真实云端转发位置与完整地图实时刷新。
- KR5/ASR-TTS 调试：本轮未触碰，保持 stub/未验证。
- KR6/手控与寻路：本轮未触碰，继续保持 `safe_to_control=false`、`robot_control_executed=false` 边界。
- 已完成 KR 历史归档：无。O7 KR 仍在当前推进区，历史记录位置为本文件、`OKR.md` 第 4.1/5/6 节和 `docs/process/okr_progress_log.md` 的 `2026-06-01 08-09` 条目。

## 本轮核心抓手

把浏览器首帧证明升级为短稳态可观测证据：30s 采样、远端 `/health` 指标、FPS 估算、摄像头读失败计数和关闭后 peer 清理。

## 需要做什么

1. 下一轮优先把 30s 扩展到 3-5 分钟稳定性，记录 FPS/延迟/CPU/温度曲线、浏览器 console/page error、断开重连和 camera release。
2. 设计真实产品播放入口的安全确认、鉴权、会话生命周期和失败分类，避免 PC endpoint 自动创建 WebRTC 或发送控制。
3. 后续再进入弱网、TURN、公网云 relay、真实用户浏览器/手机体验验证。

## 优先级和验收口径

- P0：3-5 分钟 same-LAN Chromium 稳定性，验收为首帧后连续采样、`estimated_fps` 可解释、远端 `temperature_celsius`/RSS/load 可见、关闭后 `post_close_active_peer_connections=0`。
- P1：断开重连与失败分类，验收为超时、远端不可达、camera open/read failure、peer cleanup failure 均有机器可读分类。
- P2：产品入口安全边界，验收为默认只读、显式触发 WebRTC、鉴权和 session close 生命周期明确。

## 对应责任 Engineer

- 主责：User Touchpoint Full-Stack Engineer，负责 PC browser smoke、WebRTC stats、PC API/UI 只读边界和产品入口。
- 支撑：Robot Software Engineer，负责板端 `/health` 指标、media stability summary 和 peer cleanup 行为。
- 只读复核：Hardware Infra Engineer，后续真实摄像头/板端资源占用与温度边界复核。
- 暂不介入：Robot Algorithm Engineer，本轮不触碰 Nav2/路线/视觉算法。

## 风险、阻塞和需要补齐的证据链

- 30s smoke 仍太短，不能证明 3-5 分钟或更长稳态。
- same-LAN 不能代表弱网、TURN、公网云 relay 或远程用户链路。
- Chromium smoke 不能代表真实 iPhone/Android、Safari/Chrome 手机体验。
- 本轮不证明 ASR/TTS、手控/Nav2、真实 robot ACK、任务下发、路线执行或垃圾投递闭环。
- 需要保留 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`，直到控制链路另有独立验收。

## 文档同步

- 本文件记录 micro sprint closeout。
- `OKR.md` 更新 O7 当前进度、优先级和完成路线。
- `docs/process/okr_progress_log.md` 追加本轮历史证据。
