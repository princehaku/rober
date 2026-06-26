# Camera source usage and motion truth

sprint_type: micro

## 实际改动

- 上车端 `onboard/scripts/local_webrtc_camera_smoke.py` 的 `/health` 新增 `source_usage` 只读诊断，通过扫描 `/proc/*/fd` 判断选中的 `/dev/video*` 是否被本服务、probe、`v4l2-ctl`、`ffmpeg` 或其它进程持有；该诊断固定 `opens_camera=false`，不会打开摄像头。
- PC `Robot Control summary` 新增 `readback_summary.camera.source_usage_status/source_usage_owner_count/source_usage_summary`，并在普通首屏相机首帧失败时区分“被进程占用”和“没人占用但底层无帧”。
- 高级诊断增加 `camera_source_usage_*` 字段，便于现场不用 SSH 也能看出 `/dev/video1` 是否独占。
- 文档同步更新 `docs/vision/board_camera_publisher.md` 与 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`：16 passed。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`：通过。
- `cd pc-tools/workstation && npm test -- App.test.ts`：134 passed。
- `cd pc-tools/workstation && npm test -- catalog.test.ts`：102 passed。
- `cd pc-tools/workstation && npm test`：236 passed。
- `cd pc-tools/workstation && npm run build`：通过；仅保留既有 Vite chunk > 500 kB warning。
- 已部署 `local_webrtc_camera_smoke.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/` 并重启 8088，相机服务监听 `0.0.0.0:8088`，PID `134992`。
- 已重启 PC Node，确认监听 `0.0.0.0:7001`，PID `17665`。

## 现场结论

- 本轮前现场实测 `/dev/video1` 的 OpenCV first-frame probe 返回 `capture_read_call_timeout`，`v4l2-ctl --stream-mmap --stream-count=1` 产物为 0 字节，说明当前问题更接近底层设备/输入/供电/采集卡无帧，不是 PC 页面独占造成的单点问题。
- 部署后直连 `http://192.168.1.11:8088/health` 和上位机代理 `http://192.168.1.11:8787/api/camera/health` 均返回 `source_usage.status=not_in_use`、`owner_count=0`、`opens_camera=false`。
- 通过 PC 7001 发起 first-frame probe 期间，summary 返回 `source_usage_status=in_use_by_probe`、`source_usage_owner_count=1`；probe 结束后重新读取 summary 回到 `source_usage_status=not_in_use`、`source_usage_owner_count=0`。
- 同一 probe 仍返回 `remote_http_status=503`、`status=first_frame_timeout`、`failure_reason=capture_read_call_timeout`、`open_ok=true`、`read_ok=false`、`backend_smoke_status=backend_no_frame_observed`，说明不是长期独占，而是当前设备底层无帧。
- 代码层已经确认自由低速自移动不把雷达新鲜度作为硬门禁：上车 API `free_roam_motion_readiness()` 只把相机 ready 作为运动硬门禁，雷达作为 `optional/blocking=false` 的降级监看材料；PC 自动扫图显示为 `雷达监看 / 可降级`。
- Nav2 当前不动的现场 blocker 仍是定位 TF 链，最近 evidence 显示 `/amcl_pose` 可观测但 `map -> odom` 未观测到，因此无法形成 `map -> base_link` 执行闭环；这不是“雷达没 ready 所以禁止动”的同一问题。

## 剩余风险

- 相机如果 `source_usage=not_in_use` 但仍无帧，需要现场检查 USB/摄像头输入/供电/采集卡或换 known-good UVC。
- Nav2 完整路线执行仍需要单独修定位 TF 链；本轮只把 blocker 讲清和避免误判为雷达硬门禁。
