# 2026-06-11 08:50 PC Camera Live Frame Evidence

## sprint_type

micro

## owner

`full-stack-software-engineer`

## 本轮目标

- 不触碰运动、Nav2、底盘或硬件配置，只验证 PC workstation 首屏的真实实时图传链路。
- 使用真实上位机 Robot API `http://192.168.1.11:8787`，通过本地 PC workstation proxy 打开 WebRTC 画面，采集 video 元素、帧回调、截图、上位机 readback 和 cleanup 证据。
- 同时确认普通用户首屏仍保持简洁五卡片，不暴露 HIL/Nav2/proof/key-values、`/cmd_vel`、`/api/base/manual`、路径检查或现场材料噪声。

## 实际改动

- 新增本 sprint 证据目录：
  - `sprints/2026.06.11_08-50_pc_camera_live_frame_evidence/tech-done.md`
  - `sprints/2026.06.11_08-50_pc_camera_live_frame_evidence/artifacts/**`
- 未修改 `pc-tools/workstation/src/**`、`pc-tools/workstation/server/**`、测试、ROS2、硬件、vendor 或运动控制代码。
- 未修改 PC 普通首屏产品风格。

## 用户旅程变化和触点收益

- 本轮没有引入新的 UI 行为；验证的是已有普通首屏旅程：输入小车地址 -> `连接/刷新` -> `打开画面` -> 看到实时画面状态 -> `关闭画面`。
- 对 operator 的收益是：不用 SSH 或直接访问上位机 API，就能从 PC 页面确认 WebRTC 图传是否真实进入浏览器 video 元素，并能明确关闭 peer/session。

## 真实 upper readbacks

保存路径：

- `artifacts/upper_camera_health.json`
- `artifacts/upper_camera_devices.json`
- `artifacts/upper_status.json`

关键结果：

- `GET /api/camera/health`：`status=ready`，初始 `active_peer_connections=0`，`active_peer_ids=[]`。
- `GET /api/camera/devices`：发现 `/dev/video0`、`/dev/video1`、`/dev/video2`，均存在且可读写。
- `GET /api/status`：camera 摘要返回 `http_status=200`、`status=ready`、`offer_path=/api/camera/offer`。

## Browser / Chrome smoke 证据

本地 PC workstation server：

- 启动命令：`PORT=8791 npm run api`
- 页面 URL：`http://127.0.0.1:8791/`
- 测试 baseUrl：`http://192.168.1.11:8787`

首屏 invariant：

- `artifacts/pc_first_screen_invariant.json`
- `artifacts/chrome_cdp_first_screen_invariant.json`
- `artifacts/pc_first_screen_chrome_headless.png`
- `artifacts/pc_first_screen_chrome_cdp_open_retry.png`

结果：

- `titleVisible=true`
- 五卡片全部可见：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`
- `forbiddenInFirstScreenScope=[]`
- 高级诊断和高级工具默认关闭。

真实打开画面证据：

- in-app Browser artifact：
  - `artifacts/pc_video_frame_evidence_opened.json`
  - `artifacts/pc_video_advanced_diagnostics_opened.json`
  - `artifacts/upper_camera_health_during_browser_open.json`
- Chrome CDP artifact：
  - `artifacts/chrome_cdp_open_retry_summary.json`
  - `artifacts/chrome_cdp_open_retry_video_frame_evidence_opened.json`
  - `artifacts/chrome_cdp_open_retry_video_frame_canvas_opened.png`
  - `artifacts/pc_camera_opened_chrome_cdp_open_retry.png`
  - `artifacts/upper_camera_health_during_chrome_cdp_open_retry.json`

关键结果：

- PC 页面诊断：`preview_status=streaming`、`failure_reason=none`、`ice_connection_state=connected`、`video_track_state=live`
- video 元素：`srcObjectExists=true`、`readyState=4`、`videoWidth=640`、`videoHeight=480`
- 帧证据：`requestVideoFrameCallbackObserved=true`，metadata `width=640`、`height=480`、`presentedFrames=11`
- playback quality：`totalVideoFrames=11`、`droppedVideoFrames=0`
- 上位机打开中：`active_peer_connections=1`，peer `77b984e67f4645808d09258a3b585c50`，`frames_read` 增长，`last_frame_width=640`、`last_frame_height=480`

图传结论：

- 真实 WebRTC 帧进入浏览器 video 元素：yes。
- 严格意义上的“可见场景内容”：有残余风险。保存的 canvas 和截图显示 video 区域为近黑画面，`nonTransparentPixels=6912` 但 `nonBlackPixels=0`、`averageRgbSum=4`。这更像真实摄像头当前环境/遮挡/曝光偏暗，不是信令或 video 绑定失败；但不能把它描述成已看清现场画面。

## Cleanup 证据

保存路径：

- `artifacts/pc_video_cleanup_after_close.json`
- `artifacts/upper_camera_health_after_browser_close.json`
- `artifacts/chrome_cdp_open_retry_video_cleanup_after_close.json`
- `artifacts/pc_camera_after_close_chrome_cdp_open_retry.png`
- `artifacts/upper_camera_health_after_chrome_cdp_open_retry_close.json`

关键结果：

- 页面 cleanup：`preview_status=stopped_by_user`、`cleanup_status=peer_closed:closed`
- 页面 video：`video_element_src_object=false`、`video_element_ready_state=0`、`video_element_size=0x0`
- 上位机 cleanup：`active_peer_connections=0`、`active_peer_ids=[]`
- last closed peer：`connection_state=closed`、`ice_connection_state=closed`、`track_stopped=true`

## 验证结果

已运行：

```bash
curl --max-time 8 -sS -D artifacts/upper_camera_health.headers http://192.168.1.11:8787/api/camera/health -o artifacts/upper_camera_health.json
curl --max-time 8 -sS -D artifacts/upper_camera_devices.headers http://192.168.1.11:8787/api/camera/devices -o artifacts/upper_camera_devices.json
curl --max-time 8 -sS -D artifacts/upper_status.headers http://192.168.1.11:8787/api/status -o artifacts/upper_status.json
PORT=8791 npm run api
git diff --check
```

PC 代码未改动，因此未运行 `npm run build` / `npm run test -- --run` / `npm run lint`；本轮验收范围是已构建 workstation 页面、真实上位机 readback、浏览器 smoke 和证据留档。

`git diff --check`：通过。

## 剩余风险 / 需要机器人或上位机侧配合

- 摄像头链路已证明有真实帧，但画面内容近黑；需要现场确认摄像头是否被遮挡、朝向是否正确、环境光是否足够，或上位机是否选中了更合适的 `/dev/video*`。
- in-app Browser 的 `tab.screenshot()` 在本 subagent thread 内对该页面连续超时；已用本机 Chrome headless/CDP 补齐页面截图。这个问题影响截图采集工具，不影响 WebRTC 帧证据本身。
- 未做跨网段、TURN/STUN、云 relay、录制、音频、真实远程网络质量验证。
- 本轮没有触碰运动控制；不证明底盘、Nav2、雷达、地图或送达任务能力。

## 完成前反思

- 需求覆盖：已保存 direct upper readbacks、浏览器打开画面、video 元素绑定、帧回调、截图、cleanup 和首屏 invariant。
- 文件范围：仅新增本 micro sprint 证据目录，没有修改禁止范围或 PC 产品首屏。
- 未处理 TODO：无代码 TODO；剩余风险集中在物理画面近黑和现场摄像头朝向/曝光确认。
- 验证缺口：没有真实“看清场景内容”的强证据；当前只能证明真实帧到达和渲染，不能证明画面内容可用于人工判断现场。
