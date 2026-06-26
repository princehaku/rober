# Camera shared MJPEG preview fallback

sprint_type: micro

## 实际改动

- PC 首屏实时画面从“只靠手动打开 WebRTC”改为：相机 readback ready 且浏览器支持 WebRTC 时自动接入共享 `recvonly` peer。
- 新增 MJPEG fallback 链路：
  - `onboard/scripts/local_webrtc_camera_smoke.py`：新增 `/mjpeg` 与 `/stream.mjpg`，复用 `SharedCameraCapture`，多个客户端共享同一个 OpenCV `VideoCapture`。
  - `onboard/scripts/upper_robot_api.py`：新增 `GET /api/camera/mjpeg`，只读流式代理 8088 camera service。
  - `pc-tools/workstation/src/server/index.ts`：新增 `GET /api/robot-control/camera/mjpeg`，只读同源代理，客户端断开时 abort 上游流。
  - `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：WebRTC 未绘帧时显示 MJPEG `<img>` fallback；MJPEG 加载后普通首屏显示 `画面可见`。
- 更新测试：
  - `onboard/tests/test_local_webrtc_camera_smoke.py` 覆盖 MJPEG part 只包装真实 JPEG bytes。
  - `pc-tools/workstation/test/catalog.test.ts` 覆盖 PC MJPEG proxy 固定只读 multipart。
  - `pc-tools/workstation/test/App.test.ts` 覆盖页面加载后自动 camera offer，以及 MJPEG load 后 UI 进入 `画面可见`。
- 更新 `docs/vision/board_camera_publisher.md`，记录共享实时预览、MJPEG fallback、真机 smoke 与边界。

## 验证结果

- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_upper_robot_api`：通过，60 tests。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/upper_robot_api.py`：通过。
- `npm test`：通过，2 个测试文件，223 个用例通过。
- `npm run build`：通过；Vite 仍有既有 bundle >500 kB 提醒。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 已部署到 `root@192.168.1.11:37878`：
  - camera service PID `123879`
  - upper API PID `123880`
  - PC Node `0.0.0.0:7001` PID `25629`
- 真机 MJPEG smoke：
  - `8088 /mjpeg`：multipart=true，JPEG header=true，JPEG SOI=true，2 秒截取约 526 KB。
  - `8787 /api/camera/mjpeg`：multipart=true，JPEG header=true，JPEG SOI=true，2 秒截取约 525 KB。
  - `7001 /api/robot-control/camera/mjpeg?...8787`：multipart=true，JPEG header=true，JPEG SOI=true，`X-Robber-Proxy=camera-mjpeg-readonly`。
- 浏览器 UI smoke：
  - 未点击“打开画面”时，首屏 `plain-camera-panel[data-state="画面可见"]`。
  - `robot-camera-mjpeg-preview` 存在，`naturalWidth=640`、`naturalHeight=480`。
  - 文案为 `画面状态：当前显示 MJPEG 实时画面。MJPEG 实时流已显示。`
- 断开释放 smoke：
  - PC MJPEG 客户端断开 3 秒后，8088 health 显示 `active_peer_count=0`、`shared_captures={}`。

## 剩余风险

- WebRTC offer 仍能创建 peer，但本轮 in-app browser 观察到 ICE 停在 `new`、WebRTC `frames_read=0`；已用 MJPEG fallback 满足现场实时可视，但 WebRTC ICE 根因未完全修复。
- 本轮只解决摄像头多人实时预览和所见即所得显示；自由移动、完整自动驾驶现场复验仍需继续推进。
