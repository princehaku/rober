# PC Camera Plain UI Current Smoke

## sprint_type

micro

## 实际改动

- 新增真实 PC/WebRTC smoke 证据：
  - `sprints/2026.06.11_14-20_pc_camera_plain_ui_current_smoke/artifacts/pc_camera_visible_video_stats.json`
- 更新 PC 文档：
  - `pc-tools/README.md`
  - `docs/product/pc_tools_workstation.md`
- 本轮没有修改 `pc-tools/workstation/src/**`、`onboard/**`、硬件/vendor 文件或硬件配置。

## 执行范围

本轮只通过 PC workstation/browser 路径连接真实上位机：

- 本机 workstation UI：`http://127.0.0.1:5173/`
- 本机 workstation API：`http://127.0.0.1:8787`
- 真实上位机 Robot API：`http://192.168.1.11:8787`

只执行了允许动作：连接/刷新、打开实时画面、关闭实时画面、DOM 读取和 video 元素统计。未执行 `/api/base/manual`、`/cmd_vel`、Nav2 start、非零运动或 WAVE ROVER UART。本轮 PC 证据只证明 video 元素和 `640x480` 帧流到达，不证明画面内容可见；同轮硬件/OpenCV 证据仍显示 `/dev/video1` near-black。

## 验证结果

### 指定测试

```text
cd pc-tools/workstation && npm run test -- test/App.test.ts -t "renders Robot Control V1"

Test Files  1 passed (1)
Tests  1 passed | 12 skipped (13)
Duration  4.04s
```

### 真实上位机可达性

```text
curl --max-time 3 http://192.168.1.11:8787/api/status
```

结果摘要：HTTP JSON 返回成功，`camera.status=ready`、`camera.offer_path=/api/camera/offer`。

### PC/WebRTC 链路 smoke

证据文件：`artifacts/pc_camera_visible_video_stats.json`。

打开图传期间，PC DOM/video 统计显示链路活跃：

- `video.present=true`
- `video.visible=true`
- `video.videoWidth=640`
- `video.videoHeight=480`
- `video.readyState=4`
- `video.paused=false`
- `video.currentTime=376.085`
- `canvases=[]`

以上字段中的 `video.visible=true` 只表示 HTML video 元素在页面上可见，`videoWidth/videoHeight/currentTime` 只表示帧流到达和播放时间推进；本轮没有像素 luma stats，不能证明画面内容可见。

关闭图传后：

- 点击 `关闭画面` 成功，`cleanup_attempt.clicked=true`
- `preview_status=stopped_by_user`
- `ice_connection_state=closed`
- `video_track_state=stopped`
- `cleanup_status=peer_closed:closed`
- `video.readyState=0`
- `video.videoWidth=0`
- `video.videoHeight=0`

### 普通首屏复核

证据文件：`artifacts/pc_camera_visible_video_stats.json` 的 `first_screen_contract`。

- 可见首屏组合包含 `Rober 小车控制台`。
- `.simple-user-console` 内五卡片为：`小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。
- `.simple-user-console` 默认可见文本未命中：`HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`定位重置`、`AMCL`、`task_id`、`Mock`、`检查路径`。
- DOM 事实：标题 `Rober 小车控制台` 位于 `robot-console` section head/topbar；五卡片位于 `.simple-user-console`。这与现有 `App.test.ts` 的 `visiblePlainHomeText()` 口径一致，未判定为产品代码 bug。

### git diff check

```text
git diff --check
```

结果：通过，无输出。

## 剩余风险

- 浏览器裁剪截图在 video clip 阶段出现 `Page.captureScreenshot` timeout，因此本轮没有像素 luma 统计；证据边界降级为 video/canvas DOM stats、video intrinsic size、readyState/currentTime 和 cleanup diagnostics，只能证明图传链路/视频元素活跃，不能证明内容可见。
- PC summary 连接状态显示 `有异常`，原因是上位机只读摘要中存在被 fail-closed 扫描阻断或失败的字段；本轮未展开修复，因为任务目标是图传链路和普通首屏复核，且禁止擅自重做 PC 风格。
- 本轮没有证明真实手机、真实运动、Nav2 执行、HIL pass、WAVE ROVER UART 或 delivery success。
