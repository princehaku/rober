# PC 相机 UVC 重载与 I/O 模式复验 micro sprint

sprint_type: micro

## 实际改动

- 继续围绕 PC 实时图传缺口做真实上位机恢复尝试：停止 `trashbot-local-webrtc-camera.service`，解绑 DV20 同复合设备 audio 接口，USB `3-1` reauthorize，重载 `uvcvideo`，临时使用 `quirks=0 nodrop=1 timeout=15000` 复测首帧。
- 直接用 `v4l2-ctl` 抓 `MJPG 640x480@30` 与 `YUYV 320x240@20`，结果均为 `VIDIOC_STREAMON returned 0` 但输出文件 `size=0`。
- 恢复保守 UVC 参数 `quirks=0 nodrop=0 timeout=5000`，重新启动 `trashbot-local-webrtc-camera.service`，服务恢复为 `active`。
- 补做 I/O 模式排查：`mmap` 与 `userptr` 对 MJPG/YUYV 均为 STREAMON 成功但 0 字节；当前上车 `v4l2-ctl` 不支持 `--stream-read`，read 模式未能执行。
- 同步 PC 产品文档和 OKR 进度日志，记录该方向已排除，避免后续继续把问题归因到页面独占、CMA、USB full-speed、UVC 参数或单一 mmap 模式。

## 验证结果

- 通过：上位机四个服务仍为 `active`：`trashbot-upper-robot-api.service`、`trashbot-local-webrtc-camera.service`、`trashbot-esp32-bridge.service`、`trashbot-lidar-lifecycle.service`。
- 通过：PC 7001 继续监听 `0.0.0.0:7001`。
- 通过：PC `live-summary` 返回 `status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`keyboard_motion_evidence_complete=true`。
- 未通过：相机复测仍返回 `proxy_status=probe_failed`、`status=probe_total_timeout`、`frame_observed=false`、`source_diagnosis_status=uvc_no_frame_not_exclusive`。

## 剩余风险

- 实时图传仍未完成，不能宣称 PC 端可以看到真实视频。
- 当前证据显示 DV20 设备枚举、USB 480M、无占用、CMA、UVC 参数、mmap/userptr I/O 模式和 PC relay 均不是主因；剩余更集中指向 DV20 上游视频输入源、视频线、接口、供电、采集卡/摄像头本体，或需要换 known-good UVC 复测。
- 地图和 WASD 当前可用，但 WAVE ROVER `T=1001 L/R=0/0` 仍不能宣称 wheel raw 非零。
