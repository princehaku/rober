# Camera 共享预览与 Nav2 Gate 现场诊断

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 新增同一 `video_source` 的共享 OpenCV capture，多个 WebRTC peer 不再各自独占打开 `/dev/video1`。
  - 新 offer 前自动释放卡在 `connection_state=new` / `ice_connection_state=new` 且 0 帧超过 30s 的 stale peer。
  - `close_peer` 改为释放 peer 持有的共享引用；最后一个 peer 关闭时才 release 底层 capture。
  - `/health` 增加 `media_diagnostics.shared_captures`，便于现场判断是否仍有句柄占用。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 覆盖同源多客户端只创建 1 个 `VideoCapture`。
  - 覆盖 0 帧 stale peer 自动 close 并释放 capture。
- `docs/product/pc_tools_workstation.md`
  - 记录 8088 共享 capture 与 stale peer 清理行为边界。
- `docs/product/pc_free_roam_mapping_design.md`
  - 明确小车低速移动不依赖雷达；自动/自助建图才继续看 camera/radar readiness、停止兜底和覆盖状态。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/tests/test_local_webrtc_camera_smoke.py`
- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`
  - `Ran 13 tests`
- 通过真机部署：
  - `scp ... local_webrtc_camera_smoke.py root@192.168.1.11:/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`
  - 远端 `python3 -m py_compile /root/rober/onboard/scripts/local_webrtc_camera_smoke.py`
  - 重启 8088 camera service，新 PID `114066`
- 通过真机 health：
  - `http://127.0.0.1:8088/health`
  - `status=ready`
  - `video_source=/dev/video1`
  - `active_peer_count=0`
  - `shared_captures={}`
  - `last_offer_error=null`
- 通过 PC 代理 camera probe：
  - `POST http://127.0.0.1:7001/api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787`
  - `proxy_status=probe_forwarded`
  - `remote_http_status=200`
  - `status=frame_read`
  - `open_ok=true`
  - `read_ok=true`
  - `visible_content_candidate=true`
  - `sample_path=/root/rober/onboard/runtime/camera/first_frame_probe_1782456039614.jpg`
- 通过 PC 代理 Nav2 preflight 复查：
  - `POST /api/robot-control/nav2/goal/preflight?baseUrl=http://192.168.1.11:8787`
  - `blocked_reasons=[]`
  - `localize_proof_latest/nav2_proof_latest/nav2_status` 均 `request_status=loaded`
  - `map_to_base_link=true`
  - `path_generated=true`
  - `path_point_count=36`

## 剩余风险

- 本轮没有从命令行直接发送 `Nav2 goal execute`，因为缺少现场人员在旁安全确认；Nav2 真车是否继续移动需在 PC 首屏勾选安全确认后点击 `执行图上路线`，再读取 `nav2/goal/execution/latest` 的反馈样本和结果。
- 摄像头已证明首帧可读、旧 peer 已释放，但 WebRTC 多客户端真实浏览器画面仍需至少两个浏览器窗口同时打开验证。
- 自动/自助建图仍未宣布完成：当前 live `free_roam_autonomy_latest` 仍显示 `artifact_only=true`、`cmd_vel_publish_enabled=false`，下一轮需要继续查上车端自动扫图参数 unlock 和 camera/radar readiness gate。
