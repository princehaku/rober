# O7 camera service start and long stability 产品收口

## sprint_type

micro

## 本轮时间

- 时间窗口：2026-06-02 18:33-18:41 CST
- 收口时间：2026-06-02
- Owner：full-stack-software-engineer
- Product closeout：product-okr-owner
- 本轮目标：只做 O7 事实收口，不改产品代码，不提交 git。

## 用户价值和产品北极星

O7 的用户价值是让运营人员可以在 PC workstation 上验证真实视频链路是否足够稳定，再决定能否进入远程调试、人工接管和真实用户浏览器验收。北极星仍是低成本垃圾投递机器人在普通用户手机和运营 PC 上可观测、可解释、可恢复。

本轮价值不是证明视频能力完成，而是把 O7 blocker 从“服务没启动/没监听”推进到“服务 readiness 已满足，但浏览器 `/offer` 阶段摄像头打开失败”。这让下一步修复目标从泛化启动问题收敛到板端 camera source、权限、占用或驱动状态。

## OKR 映射和方向判断

- Objective：O7 PC 端运营调试与数据训练平台。
- 当前进度：保持约 96%，不上调。
- 方向判断：继续。
- 切换原因：O1 仍是最低 Objective，但当前 blocker 为 `target_port_identity_possible_lidar_or_other_stc_before_more_T130`，必须现场物理拔插/追线确认，不能继续用软件 sprint 重复消费同一根因；本轮按 repeated-blocker rule 切到 O7 的可推进真实材料缺口。
- blocker 迁移：`remote_script_present_but_service_inactive` -> `camera_service_ready_but_first_frame_timeout_offer_http_500`。

## 实际改动

本轮 Product closeout 只更新事实文档与 OKR 记录。前序 full-stack worker 已留下的代码/docs事实如下：

- readiness collector 允许 operator-run 启动脚本时，即使缺 systemd unit，只要 HTTP `/health` 和 `/devices` 可达、SSH 可达、8088 listening、process hint 和 remote script present，就进入 `ready_for_long_stability=true`。
- 缺 systemd unit 不再作为 180s 采集 blocker，但继续作为生产化风险记录。
- 本轮 Product 不修改产品代码、测试代码、硬件配置、launch 参数或业务实现。

## 验证结果

### Full-stack 复验（2026-06-02 19:12-19:14 CST）

本轮只复验 O7 readiness / long-stability 收口事实，不自动 SSH 启动服务，不 POST `/offer`，不创建 WebRTC session，不触碰 O1 串口、WAVE ROVER、T=130/T=1/T=13/T=131、`cmd_vel` 或硬件配置。

```text
cd pc-tools/workstation && npm run o7:camera-service-readiness -- --dry-run
exit=0
status=dry_run
network_probe_executed=false
ssh_probe_executed=false
post_executed=false
webrtc_session_created=false
offer_executed=false
artifact_written=false
blocked_reasons=["dry_run_no_network_no_ssh_no_post_no_webrtc_no_artifact"]

cd pc-tools/workstation && npm run test -- catalog.test.ts
exit=0
Test Files 1 passed (1)
Tests 57 passed (57)

cd pc-tools/workstation && npm run build
exit=0
vite built dist/index.html and bundled assets successfully

cd pc-tools/workstation && npm run lint
exit=0
```

### Camera service readiness artifact

证据文件：`.workstation-runtime/o7-camera-service-readiness.json`。

关键结论：

```text
status=ready_for_long_stability
health.status=reachable
health.http_status=200
devices.status=reachable
devices.http_status=200
ssh.status=reachable
camera_port_listening=true
process_hint=python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 ...
safe_to_control=false
sends_commands=false
robot_control_executed=false
```

Product 判定：readiness 已从上一轮 `remote_script_present_but_service_inactive` 推进到可进入 long-stability 采集的状态；缺 systemd unit 仅保留为断电/重启自恢复未证明的生产化风险。

### Browser long stability artifact

证据文件：`.workstation-runtime/o7-browser-playback-smoke.json`。

关键结论：

```text
status=failed
failure_category=first_frame_timeout
remote_health_status=ready
start_clicked=true
offer_executed_by_browser=true
offer_http_status=500
first_frame_received=false
observation_window_ms=30605
stability_summary.status=not_observed
safe_to_control=false
sends_commands=false
robot_control_executed=false
```

Product 判定：浏览器已触发 start 和 `/offer`，但板端返回 HTTP 500，未拿到首帧，未进入 180s/3-5min 稳定性窗口。本轮不能证明真实长期视频能力完成，O7 保持约 96%。

## KR 拆解和验收口径

- 当前 KR 抓手：真实 PC browser long-stability 材料采集。
- 本轮已关闭：readiness 前置从“服务未启动/未监听”关闭为 ready。
- 本轮未关闭：180s/3-5min 首帧和稳定性材料。
- 下一轮验收口径：修复 camera source 打开失败后，重跑 browser long stability；只有 `first_frame_received=true`、`stability_summary.observation_window_ms >= 180000`、连接/ICE/video/cleanup 条件同时满足，才能作为 O7 真实长稳材料。

## 对应责任 Engineer

- 主责：full-stack-software-engineer。
- 需要协作：如果 camera source `0` 涉及板端设备枚举、权限、驱动或占用，转 robot-hardware-engineer 做只读事实补充；若涉及 ROS2 或控制链路，不在本轮处理。

## 剩余风险

- 未获得真实 180s/3-5min O7 browser long-stability artifact；O7 真实视频能力仍 `not_proven`。
- `/offer` HTTP 500 与首帧超时需要继续定位，优先检查板端 camera source、权限、占用、驱动状态和启动参数。
- 当前 camera service 是 operator-run/nohup 进程，不是 systemd 持久化服务；断电/重启自恢复仍未证明。
- 公网 cloud relay、TURN/弱网、鉴权、真实手机浏览器、ASR/TTS、手控/Nav2、robot ACK 和完整上车任务闭环仍未证明。
- O1 当前最低 Objective 仍被 `target_port_identity_possible_lidar_or_other_stc_before_more_T130` 锁住，需要现场物理拔插/追线证据后再继续。

## 已完成 KR 历史记录

本轮没有 KR 达到可归档完成条件；没有把任何 O7 KR 移入历史完成区。历史记录位置为本文件、`OKR.md` 第 4/4.1/5 节，以及 `docs/process/okr_progress_log.md` 的 `2026-06-02 18-19` 条目。
