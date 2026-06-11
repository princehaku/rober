# Camera Service 上板部署与 no-motion smoke

## sprint_type

micro

## 背景

继续推进真实上车 evidence capture 的实时图传缺口。上一轮已把
`onboard/scripts/local_webrtc_camera_smoke.py` 入仓，本轮直接部署到真实上位机
`root@192.168.1.11:37878`，目标是确认 8088 camera service 可由仓库版本复现，
并验证 PC/Robot API 使用的 camera health/devices/offer/close 合同。

本轮不调用 `/api/base/manual`、不发布 `/cmd_vel`、不执行 Nav2 goal、不打开
WAVE ROVER UART，不触碰 `/dev/ttyS5`。

## 实际改动

- 修复 `onboard/scripts/local_webrtc_camera_smoke.py` 的 UVC 复合设备识别：
  - DV20 `/dev/video1` 的全局 Capabilities 同时包含 `Video Capture` 和
    `Metadata Capture`，但它的 `Device Caps` 与格式表实际是图像采集。
  - 现在以 `Format Video Capture`、`MJPG`、`YUYV` 等真实图像帧格式作为
    video capture 判定依据，不再因 capability 文本出现 metadata 就误判。
- 新增单元测试锁定该真实板端场景：
  - `test_uvc_capture_with_metadata_capability_still_counts_as_video`
- 新增本轮上板 artifacts：
  - `artifacts/01_remote_backup_sha.txt`
  - `artifacts/02_deploy_restart_status.txt`
  - `artifacts/03_health_devices_raw.jsonl`
  - `artifacts/04_local_fixed_sha.txt`
  - `artifacts/05_fixed_deploy_restart_status.txt`
  - `artifacts/06_fixed_health_devices_raw.jsonl`
  - `artifacts/07_offer_close_smoke.json`
  - `artifacts/08_cleanup_status_journal.txt`

## 上板部署结果

- 部署前远端脚本 hash：
  - `f77e1b5ee942de322afdb5b4dd18df0a369e7e3c4be4c0c2b9ab9735f719f8f6`
- 首次部署仓库版本 hash：
  - `db538da86535d6a5e87ae6ebe3f9ac3b7ab047555e727dd25eea69f2f6fc891d`
- 真实板端 smoke 暴露 auto 选源 bug：
  - `/dev/video0`：Cedrus decoder，负分。
  - `/dev/video1`：被误判为 metadata，导致 `status=no_video_source`。
  - `/dev/video2`：metadata，负分。
- 修复后本地与远端 hash 一致：
  - `12ae0bf6798f08991ac7daa587c181c84af6bbf8436bc80d0c8dbe4ba72d6611`
- `trashbot-local-webrtc-camera.service` 与 `trashbot-upper-robot-api.service`
  均为 `active`。

## 真实 health/devices 结果

修复后，直接 8088 与经 8787 Robot API 代理读回均一致：

- `/health`
  - `schema=trashbot.local_webrtc_camera_smoke.v1`
  - `status=ready`
  - `video_source=/dev/video1`
  - `video_source_mode=auto`
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `active_peer_count=0`
- `/devices`
  - `schema=trashbot.local_webrtc_camera_devices.v1`
  - `status=loaded`
  - `video_source=/dev/video1`
  - `paths=["/dev/video0","/dev/video1","/dev/video2"]`
- auto 选择摘要：
  - `/dev/video0`：`selection_score=-895`，`is_decoder=true`
  - `/dev/video1`：`selection_score=148`，`is_video_capture=true`
  - `/dev/video2`：`selection_score=-1055`，`is_metadata=true`

## 真实 offer/close 结果

本轮在上位机本机用 `aiortc` 创建 recvonly offer，POST 到 `http://127.0.0.1:8088/offer`。

结果：

- `offer_http_status=503`
- `offer_schema=trashbot.local_webrtc_camera_smoke.v1`
- `offer_error=first_frame_unreadable`
- `offer_failure_reason=first_frame_timeout`
- `offer_video_source=/dev/video1`
- `peer_id=None`
- `health_after.status=ready`
- `health_after.video_source=/dev/video1`
- `health_after.active_peer_count=0`
- `health_after.media_diagnostics.last_offer_error.failure_reason=first_frame_timeout`

结论：新服务已正确选择 `/dev/video1`，但真实首帧仍不可读；服务按设计
fail-closed，没有伪造图像，没有创建残留 peer。

## 验证命令

本地验证：

```bash
python3 -m unittest discover onboard/tests -p '*camera*'
python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py
git diff --check
```

结果：

- `Ran 10 tests ... OK`
- `py_compile` 通过
- `git diff --check` 通过

远端验证：

```bash
ssh -p 37878 root@192.168.1.11 'python3 -m py_compile /root/rober/onboard/scripts/local_webrtc_camera_smoke.py'
ssh -p 37878 root@192.168.1.11 'systemctl restart trashbot-local-webrtc-camera.service'
ssh -p 37878 root@192.168.1.11 'curl http://127.0.0.1:8088/health'
ssh -p 37878 root@192.168.1.11 'curl http://127.0.0.1:8088/devices'
ssh -p 37878 root@192.168.1.11 'curl http://127.0.0.1:8787/api/camera/health'
ssh -p 37878 root@192.168.1.11 'curl http://127.0.0.1:8787/api/camera/devices'
ssh -p 37878 root@192.168.1.11 'python3 aiortc recvonly offer smoke'
```

清理验证：

- `trashbot-local-webrtc-camera.service=active`
- `trashbot-upper-robot-api.service=active`
- `active_peer_count=0`
- `lsof/fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5` 无残留占用输出

## 剩余风险

- `/dev/video1` 仍然 `first_frame_timeout`，PC 实时图传可见内容没有恢复。
- 当前缺口继续指向 DV20 物理输入源、线缆、采集卡状态、供电、光照/遮挡或已知可用 UVC 替换验证。
- 运动 HIL gate 仍缺 `visible_content_proven=true`、外部视频、轮速反馈非零和 LiDAR motion delta，不能放行非 stop 运动。
