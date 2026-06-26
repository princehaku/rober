# Camera 探针近黑画面 WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 首帧探针复用浏览器视频帧同一可见阈值：`mean_luma >= 18`、`max_luma >= 96`、`non_black_ratio >= 0.05` 才算可用画面。
  - 当上位机 camera probe 已读到样张但亮度不足时，普通首屏显示 `画面偏暗`，提示检查镜头/光线。
  - 近黑样张不再作为 `latestCameraProbeSampleRef()` 输出，避免 `记录当前画面` 或送达材料预填把黑图保存成 `visible_content_proven=true`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增低亮 camera probe 回归：真机同形 `mean_luma=6.5746`、`max_luma=21`、`non_black_ratio=0.178014` 时，UI 显示偏暗，记录按钮禁用，且不会调用 operator report、Nav2、manual、delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 camera probe 亮度 WYSIWYG 与材料 gate 边界。

## 现场诊断依据

- 真机 `GET http://192.168.1.11:8088/health` 返回 `status=ready`、`video_source=/dev/video1`、`active_peer_count=0`、`shared_captures={}`。
- PC 代理 `POST /api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787` 返回：
  - `proxy_status=probe_forwarded`
  - `status=frame_read`
  - `open_ok=true`
  - `read_ok=true`
  - `visible_content_proven=true`
  - `sample_path=/root/rober/onboard/runtime/camera/first_frame_probe_1782468144317.jpg`
  - `mean_luma=6.5746`
  - `max_luma=21`
  - `non_black_ratio=0.178014`
- PC 代理 `GET /api/robot-control/camera/mjpeg?baseUrl=http://192.168.1.11:8787` 可输出 `multipart/x-mixed-replace`，并在前 4096 字节内读到 JPEG SOI，说明共享 MJPEG 兜底链路通，但当前画面很暗。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "camera|画面|MJPEG|low-light|near-black"`
  - `Test Files 1 passed`
  - `Tests 15 passed | 111 skipped`
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed`
  - `Tests 225 passed`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - 仅保留既有 Vite chunk size warning。

## 剩余风险

- 本轮修复 PC WYSIWYG 与材料 gate，不改变相机硬件曝光、镜头遮挡或现场光照。
- 真实浏览器双窗口同时观看仍建议现场复测；当前命令行已证明 8088 health、PC first-frame probe 与 PC MJPEG 代理都可读。
- 自动/自助建图仍未宣称完成；本轮只推进“画面必须所见即所得”。
