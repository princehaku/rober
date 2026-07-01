# PC Camera Probe Timeout Guard

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：把 PC 端 `camera/first-frame/probe` 代理等待窗口调整为普通只读复测 `60s`、显式 backend smoke 诊断 `75s`；相机代理 fetch 遇到 `TimeoutError` / `AbortError` 时统一返回 `fetch_timeout_<ms>ms`，并在失败响应里保留规范化后的小车地址，避免现场误判为 baseUrl 未加载。
- `pc-tools/workstation/test/catalog.test.ts`：新增相机首帧 probe 超时合同测试，覆盖普通复测与 `backendSmoke=1` 两条路径，确认不丢 `normalized_base_url`、不把只读复测标成已控制机器人。
- `docs/product/pc_tools_workstation.md`：同步记录 PC 相机首帧探针的 no-motion 超时合同和禁止动作边界。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts -t "camera first-frame probe"`，结果 `1 passed`、`4 passed | 177 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 仍提示主 chunk 超过 500 kB，这是既有体积警告，不影响本轮相机探针合同。
- 通过：`npm test`，结果 `3 passed`、`419 passed`。
- 通过：`git diff --check`。
- 通过：重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 Node `*:7001`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：真实上车 no-motion 复测 `POST /api/robot-control/camera/first-frame/probe` 返回 `proxy_status=probe_failed`、`status=first_frame_timeout`、`normalized_base_url=http://192.168.1.11:8787`、`remote_http_status=503`、`failure_reason=deadline_expired`、`robot_control_executed=false`，并带回 `fallback_attempt_count=8` 与多组 MJPG/YUYV fallback 摘要；PC 代理不再提前 abort。
- 通过：`GET /api/robot-control/summary` 读回相机仍为 `source_first_frame_failed`、`camera_usb_speed=12M`、`camera_hardware_action_required=true`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`；地图可见、雷达 ready，当前 WYSIWYG 缺口只剩 camera。
- 通过：`GET /api/robot-control/camera/mjpeg/status` 读回 `exclusive_camera_claim=false`、`client_count=0`、`cached_frame_loaded=false`、`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`。

## 剩余风险

- 当前真实上车相机仍因为 DV20/UVC 接在 USB 12M full-speed 链路上无法出首帧；本轮只修 PC 代理等待和错误解释，不宣称摄像头硬件链路已恢复。下一步仍是换高速 USB 口/线或 known-good UVC 后再复测。
- 本轮不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`，不改变小车运动状态。
