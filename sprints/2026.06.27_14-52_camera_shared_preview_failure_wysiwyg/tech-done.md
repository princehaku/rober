# 2026.06.27 14:52 共享预览失败态 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 共享画面状态在已知相机源首帧失败、MJPEG 上游超时、HTTP 5xx 或 health 无首帧时，不再追加 `页面正在接入共享预览`。
  - 相机 ready 且无已知失败时仍保留接入提示，表达多页面共用同一条上游流。
- `pc-tools/workstation/test/App.test.ts`
  - 更新共享预览失败态断言，锁定“不是独占/无首帧/上游无画面”优先于“正在接入”。
- `docs/product/pc_tools_workstation.md`
- `docs/vision/board_camera_publisher.md`

## 验证结果

- 已通过：`npm test -- --run App.test.ts -t "shared camera|shared preview|MJPEG upstream|source first-frame"`，8 个相关用例通过。
- 已通过：`npm test`，291 个测试通过。
- 已通过：`npm run build`，Vite 仍有既有 chunk size 警告。
- 已通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，PC Node 继续监听 `*:7001`。
- 已通过：只读 `GET /api/robot-control/summary?robot_base_url=http://192.168.1.11:8787`：
  - `camera.status=source_first_frame_failed`
  - `shared_preview_client_count=0`
  - `shared_preview_upstream_active=false`
  - `shared_preview_content_type_loaded=false`
  - `shared_preview_exclusive_camera_claim=false`
  - `shared_preview_last_failure_reason=camera_source_first_frame_failed`
  - `source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `source_usage_status=not_in_use`
  - `source_usage_owner_count=0`
- 已通过：只读 `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回 `status_loaded`，`client_count=0`，`upstream_active=false`，`exclusive_camera_claim=false`；status 端点无 latest failure 时，测试覆盖 UI 回退 summary/health 无首帧分支。
- 已通过：`curl -fsS http://127.0.0.1:7001/` 返回首页 HTML。

## 剩余风险

- 本轮只修 PC 首屏共享预览文案，不触发真实 camera probe、WebRTC offer、Nav2、manual、keyboard、free-roam 或 `/cmd_vel`。
- live 摄像头仍是 DV20 `/dev/video1` 能枚举但无首帧；真实恢复需要检查 USB、摄像头输入/供电或换 known-good UVC 设备。
