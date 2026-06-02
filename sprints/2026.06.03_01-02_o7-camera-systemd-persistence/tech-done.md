# O7 Camera Systemd Persistence Micro Sprint

## sprint_type

micro

## 实际改动

- 新增 `onboard/systemd/trashbot-local-webrtc-camera.service`，把 O7 LAN-only local WebRTC camera smoke 固定为可版本化 systemd unit 模板。
- 新增 `onboard/scripts/install_o7_camera_service.sh`，支持 `--dry-run`、`--no-enable`、`--no-start`、自定义 repo root/systemd dir；默认只安装并启动 8088 camera smoke，固定声明不打开串口、不发送 WAVE ROVER JSON、不启动 ROS2/Nav2、不发送 `/cmd_vel`。
- 扩展 `pc-tools/workstation/scripts/o7-camera-service-readiness-collector.mjs`，只读 SSH 探测新增 `systemctl show trashbot-local-webrtc-camera.service`，输出 `systemd_unit`、`service_unit_installed`、`service_unit_active`，并细分 `service_unit_not_installed` / `service_unit_inactive`。
- 更新 `pc-tools/workstation/src/server/realMaterialAcceptance.ts` 和 O7 readiness 测试，让真实材料验收队列优先提示安装/重启固定 unit，而不是继续依赖 operator-run/nohup。
- 同步更新 `docs/interfaces/o7_local_webrtc_camera_smoke.md` 和 `docs/interfaces/real_material_acceptance_queue.md`，明确 systemd 入口、安全边界和 readiness 分类。

## 验证结果

Full-Stack 子 agent 已执行：

- `bash -n onboard/scripts/install_o7_camera_service.sh`：通过。
- `bash onboard/scripts/install_o7_camera_service.sh --dry-run --no-start`：通过；输出包含 `defaults=HOST=0.0.0.0 PORT=8088 ROBER_CAMERA_SOURCE=auto`、`safety=no_serial_no_wave_rover_json_no_ros2_no_cmd_vel`，只打印 dry-run 的 `systemctl daemon-reload/enable`。
- `cd pc-tools/workstation && npm run build`：通过；cleanup 子 agent 复验通过。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files 2 passed (2)`、`Tests 63 passed (63)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 lint error。
- `git diff --check -- pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/src/env.d.ts pc-tools/workstation/test/script-modules.d.ts`：通过，无 whitespace 问题。
- 本轮范围 diff check：通过，无 whitespace 问题。

远端非运动检查证据：

- SSH 目标 `root@192.168.1.11 -p 37878` 可达，主机为 `op-z3-b6.home`。
- `0.0.0.0:8088` 已监听，进程为 `python3`。
- `curl http://127.0.0.1:8088/health` 返回 `status=ready`、`video_source=/dev/video1`、`imports aiohttp/aiortc/cv2/av=true`、`safe_to_control=false`。
- readiness collector 输出 `status=ready_for_long_stability`，HTTP `/health` 和 `/devices` reachable，SSH reachable，8088 listening。
- 首次安装后发现旧 operator-run `python3` 进程 `pid=4135` 占用 8088，导致新 systemd unit bind 失败重启；随后只确认并停止该 `local_webrtc_camera_smoke.py` 旧进程，未停止其他 Python/ROS/系统进程。
- `systemctl restart trashbot-local-webrtc-camera.service` 后，`is-enabled=enabled`、`is-active=active`、`LoadState=loaded`、`ActiveState=active`、`SubState=running`、`MainPID=21250`。
- `ss -ltnp` 显示 `0.0.0.0:8088` 由 `python3 pid=21250` 监听，listener pid 与 systemd unit `MainPID=21250` 一致。
- `/health` 返回 `status=ready`、`video_source=auto`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`。

## OKR 影响

- 本轮推进 O7：从“只有 operator-run/nohup 风险”推进到“仓库内已有 systemd persistence 入口，远端 unit 已 installed/enabled/active，PC readiness 能识别固定 unit 状态”。
- O7 建议从约 97% 上调到约 97.5%。原因：远端 8088 已由 `trashbot-local-webrtc-camera.service` 的 `MainPID` 接管并返回 health ready，关闭了当前“服务未守护/重启不可恢复”缺口的一部分。
- 该上调不等于生产视频链路完成；本轮没有证明 reboot 后自恢复、browser 180s long-stability、生产 relay/TURN/auth、手机公网、弱网、ASR/TTS、手控/Nav2、robot ACK 或完整上车任务闭环。
- O1 仍是最低 Objective，但同一 STC/LiDAR 端口身份 blocker 已重复消费；本轮按 repeated-blocker rule 不继续盲发 `T=130`，等待现场物理追线/分别拔插 LiDAR 与 WAVE ROVER 控制器后再推进。

## 剩余风险

- 远端 `trashbot-local-webrtc-camera.service` 已确认 installed/enabled/active，但没有 reboot 后自恢复证据。
- 远端 8787 workstation API 仍未监听。
- 本轮没有运行新的 180s browser long-stability collector；已有 8088 health 只能证明当前 camera smoke HTTP 服务在线。
- 没有触发 `/offer`、没有创建 WebRTC session、没有打开串口、没有发送 `T=130/T=131/T=1/T=13`、没有发送 `/cmd_vel`、没有启动 ROS2/Nav2/WAVE ROVER、没有执行机器人运动控制。

## Product Closeout

- OKR 映射：Objective 7。
- 方向判断：继续。
- 进度口径：O7 保持约 97.5%。systemd persistence 价值已计入该进度：`trashbot-local-webrtc-camera.service` installed/enabled/active，8088 health ready，unit `MainPID` 与 listener pid 一致。
- 最新边界：后续 PC 首屏 smoke 已发起 `/offer` 1 次，但远端 `active_peer_connections=1` 导致 `409 Conflict`，video 无首帧；这不推翻 systemd persistence 证据，但也不能宣称首屏首帧成功或生产视频链路完成。
- 下一轮优先级：camera peer cleanup/独占首帧复验、reboot 后自恢复、browser 180s long-stability 复跑、远端 8787 workstation API、云 relay/TURN/auth 和 phone/browser production path。
