# PC camera MJPEG shared status alias

## sprint_type

micro

## 实际改动

- `/api/robot-control/camera/mjpeg/status` 新增与 summary 对齐的共享预览 alias：
  `shared_preview_client_count`、`shared_preview_upstream_active`、`shared_preview_content_type_loaded`、`shared_preview_cached_frame_loaded`、`shared_preview_cached_frame_age_ms`、`shared_preview_shared_capture`、`shared_preview_exclusive_camera_claim`、`shared_preview_contract`、`shared_preview_last_failure_reason`、`shared_preview_last_remote_http_status`、`shared_preview_last_failure_at_ms`。
- 独立相机状态接口现在也能直接证明“多个页面共享同一条上游流，不是浏览器独占”，避免只读 `shared_preview_*` 的脚本拿到 null。
- 前端 fixture、合同测试、`pc-tools/README.md` 和 `docs/product/pc_free_roam_mapping_design.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "MJPEG"`
  - `Test Files 1 passed (1)`
  - `Tests 10 passed | 148 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍有既有 chunk size warning，但 build 成功。
- 通过：本机 7001 只读 camera MJPEG status 验证。
  - 7001 监听为 workstation 的 `tsx src/server/index.ts` / `node` 进程，未触碰 Clash。
  - `curl http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status` 返回：
    `proxy_status=status_loaded`、`preview_status=source_first_frame_failed`、
    `source_diagnosis_status=uvc_no_frame_not_exclusive`、
    `preview_next_action_plain=检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`、
    `client_count=0`、`shared_preview_client_count=0`、
    `upstream_active=false`、`shared_preview_upstream_active=false`、
    `cached_frame_loaded=false`、`shared_preview_cached_frame_loaded=false`、
    `shared_capture=true`、`shared_preview_shared_capture=true`、
    `exclusive_camera_claim=false`、`shared_preview_exclusive_camera_claim=false`、
    `shared_preview_contract=single_shared_capture_for_multiple_clients`、
    `last_failure_reason=camera_source_first_frame_failed`、
    `shared_preview_last_failure_reason=camera_source_first_frame_failed`、
    `robot_control_executed=false`。

## 剩余风险

- 本轮只补本机 relay 只读状态；不新开 camera capture、不重启相机、不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- live 摄像头仍报告 `uvc_no_frame_not_exclusive` / 首帧失败，这说明当前问题不是浏览器独占；仍需现场检查 USB、摄像头输入/供电或换 known-good UVC。
