# Camera First-Frame Recovery Probe Tech Done

## Sprint Type

sprint_type: micro

## owner

`rober-hardware-engineer`

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

本轮采用的边界结论：

- `base_ctrl.py` 证明 WAVE ROVER vendor 上位机底盘控制走 UART JSON，
  默认示例是 `/dev/ttyAMA0 @ 115200`，属于底盘控制链路。
- `cv_ctrl.py` 证明 vendor 相机路径与底盘 UART 分离，USB camera 走
  `cv2.VideoCapture(...)`。
- `config.yaml` 给出 vendor 视频默认分辨率 `640x480`。
- 因此本轮 `/dev/video1` 的 UVC/V4L2 首帧 probe 不涉及 `/dev/ttyS5`、
  `T=1/T=13/T=130/T=131`、`/cmd_vel` 或任何 WAVE ROVER UART 写入。

## 实际改动

- `docs/vision/board_camera_publisher.md`
  - 新增 2026-06-11 16:05 first-frame recovery probe 记录。
- `sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/tech-done.md`
  - 记录本轮真实上位机 readback、restart 前后对比、cleanup 和风险。
- `sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/`
  - 保存 API、systemd、journalctl、v4l2、OpenCV probe 和 cleanup artifact。

## 已证实的硬件 / 服务结论

1. 当前 `/dev/video1` 在三组模式下都表现为 `opened=true read_ok=false`：
   - `MJPG 640x480`
   - `YUYV 640x480`
   - `MJPG 1280x720`
2. 重启前后的 OpenCV first-frame probe 结果一致，均复现
   `VIDEOIO(V4L2:/dev/video1): select() timeout`。
3. camera service 在重启前是 `active (running)`，重启后仍能恢复到 `active`，
   `/api/camera/health` 最终保持 `status=ready`、`active_peer_count=0`。
4. 本轮 probe 前后 `lsof/fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5`
   都无残留占用，未观察到普通的 device busy。
5. 15:57 的失败 peer 与本轮 OpenCV probe 共同指向 `/dev/video1` 首帧读取层；
   当前不再优先怀疑 PC 前端状态。
6. 因为本轮一帧都没有读到，所以不存在“near-black 但仍可读”的结论；
   当前是更前面的 first-frame read timeout。

## 验证结果

已执行的真实命令与证据：

- API readback：
  - `curl http://192.168.1.11:8787/api/camera/health`
  - `curl http://192.168.1.11:8787/api/camera/devices`
- service / log / V4L2：
  - `systemctl status trashbot-local-webrtc-camera.service`
  - `journalctl -u trashbot-local-webrtc-camera.service -n 200`
  - `v4l2-ctl --device=/dev/video1 --all`
  - `v4l2-ctl --device=/dev/video1 --list-formats-ext`
- occupancy：
  - `lsof /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5`
  - `fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5`
- first-frame probe：
  - OpenCV `VideoCapture('/dev/video1', cv2.CAP_V4L2)`，
    分别尝试 `MJPG 640x480`、`YUYV 640x480`、`MJPG 1280x720`，
    每种模式只做少量读帧。
- 安全恢复：
  - `systemctl restart trashbot-local-webrtc-camera.service`
  - restart 后再次执行 `/api/camera/health` 与同一组 OpenCV probe。

结果摘要：

- restart 前 health：
  - `last_closed_peer.source_selection.failure_reason=no_candidate_opened_and_read_first_frame`
  - `/dev/video1 opened=true read_ok=false`
- restart 前 probe：
  - 三种模式均 `opened=true read_ok=false`
  - 每种模式约 `40.7s`，四次读帧都超时
- restart 后 health：
  - `status=ready`
  - `active_peer_count=0`
  - `last_closed_peer=null`
- restart 后 probe：
  - 三种模式仍全部 `opened=true read_ok=false`
  - 继续复现 `select() timeout`

## artifact 路径

- API / service / v4l2
  - [camera_health_before.json](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/api/camera_health_before.json)
  - [camera_devices_before.json](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/api/camera_devices_before.json)
  - [camera_health_after_restart.body](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/api/camera_health_after_restart.body)
  - [camera_health_direct_8088_after_restart.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/api/camera_health_direct_8088_after_restart.txt)
  - [systemctl_status_before.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/service/systemctl_status_before.txt)
  - [journalctl_before.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/service/journalctl_before.txt)
  - [systemctl_status_after_restart.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/service/systemctl_status_after_restart.txt)
  - [journalctl_after_restart.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/service/journalctl_after_restart.txt)
  - [video1_all_before.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/v4l2/video1_all_before.txt)
  - [video1_formats_before.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/v4l2/video1_formats_before.txt)
- probe
  - [summary_before.json](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/probe/summary_before.json)
  - [summary_after.json](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/probe/summary_after.json)
  - [probe_before_console.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/probe/probe_before_console.txt)
  - [probe_after_console.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/probe/probe_after_console.txt)
- cleanup
  - [camera_health_final.json](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/cleanup/camera_health_final.json)
  - [camera_service_final.txt](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/cleanup/camera_service_final.txt)
  - [remote_device_process_cleanup_final.log](/Users/m1/apps/rober/sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/artifacts/cleanup/remote_device_process_cleanup_final.log)

## cleanup 结果

- `trashbot-local-webrtc-camera.service` 最终 `active`。
- `/api/camera/health` 最终 `active_peer_count=0`。
- `/dev/video0`、`/dev/video1`、`/dev/video2`、`/dev/ttyS5` 最终 `lsof/fuser` 无输出。
- 本轮没有对 service unit、配置、launch、firmware 或硬件默认值做修改。

## 失败定位和剩余风险

失败定位：

- 当前 root cause 更接近 DV20 `/dev/video1` 的 first-frame readback 卡死，
  而不是 PC 前端、HTTP 代理或单纯的 camera service 进程状态。
- `systemctl restart` 只能恢复 service 到 `active/ready`，不能恢复 `/dev/video1`
  首帧读取。
- 由于 probe 前后都无 device occupancy，本轮暂不支持“被别的进程抢占了 camera”这一主结论。

剩余风险：

1. 还没有直接证明是 DV20 本体、USB 口、供电、线材，还是更上游的物理输入源异常；
   这里只能把范围收窄到 `/dev/video1` / UVC 首帧层。
2. 没有首帧就没有 sample image，因此本轮不能给出“near-black”或“已恢复可见内容”的结论。
3. 后续若继续推进，需要现场做不改配置的物理履约动作：
   - 重新插拔 DV20 或切换 USB 口；
   - 若 DV20 有独立物理输入源，核对该输入是否正常出图；
   - 重新上电后复跑本 sprint 的同一组 OpenCV probe。

## 自检

- 未改 `pc-tools/**`、`onboard/**`、`docs/vendor/**`。
- 未调用 `/api/base/manual`，未发布 `/cmd_vel`，未占用 `/dev/ttyS5`。
- 未修改 service unit/config、launch、hardware defaults、firmware。
- 已把 restart 前后差异、cleanup 和风险写入文档。
