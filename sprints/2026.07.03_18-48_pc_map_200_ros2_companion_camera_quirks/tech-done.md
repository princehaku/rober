# PC Map 200% + ROS2 Companion + Camera Quirk Matrix

sprint_type: micro

## 实际改动

- PC 首页和 `/map` 地图默认缩放从 `100%` 提升到 `200%`，`适配` 保持 `45%`，最高仍为 `1200%`。
- 收敛首页地图 CSS 覆盖规则：普通驾驶台地图高度统一到 `clamp(960px, calc(100vh - 8px), 1800px)`，中宽屏断点统一到 `clamp(940px, calc(100vh - 8px), 1680px)`；地图内部 viewport 最小高度提升到 `clamp(780px, calc(100vh - 116px), 1500px)`。
- Summary/API/DOM 文案同步说明：ROS2 配套工具是本地 RViz2 和远程 Foxglove bridge + Foxglove Web；普通用户仍默认使用 PC 大地图和 `/map`，工程工具不替代简易控制台。
- 真实上位机执行 DV20 摄像头 `uvcvideo` quirk/nodrop 矩阵，覆盖 `quirks=0/2/4/16/128/256/384/640/32768/32896/33024`、`nodrop=0/1`、`MJPG@640x480@30` 与 `YUYV@320x240@20`；所有组合均为 `bytes=0`。
- quirk 矩阵结束后恢复上位机 `uvcvideo quirks=0,nodrop=0`，并确认 `trashbot-local-webrtc-camera.service=active`。
- 同步更新产品和硬件文档：
  - `docs/product/pc_tools_workstation.md`
  - `docs/product/pc_free_roam_mapping_design.md`
  - `docs/hardware/board_sensor_stack_smoke.md`

## 验证结果

- `npm test -- robotControlSummary.test.ts`：13 passed。
- `npm test -- catalog.test.ts`：188 passed。
- `npm test -- App.test.ts`：239 passed。
- `npm run build`：通过，Vite 仍提示大 chunk warning，属于既有体积提示。
- `git diff --check`：通过。
- PC 7001 已重启并监听 `0.0.0.0:7001`，当前进程 PID `16937`。
- Live summary smoke：
  - `map_display_default_zoom_percent=200%`
  - `map_display_direct_map_default_zoom_percent=200%`
  - `map_display_ros2_companion_answer_plain` 明确 RViz2/Foxglove 只作工程观察。
- 浏览器 `/map` DOM smoke：
  - `panelZoom=200%`
  - `panelDefaultZoom=200%`
  - `directDefaultZoom=200%`
  - `size=fullscreen`
  - 1280x720 视口下地图 layer 约 `1272x787`
  - 地图图像、路线、小车位置、雷达点和目标点均可见。

## 剩余风险

- 摄像头仍没有真实首帧；本轮已排除页面独占、MJPG/YUYV 单格式、低带宽格式和常见 uvcvideo quirk，剩余更像摄像头输入、USB 线/接口/供电或设备本体问题。
- wheel raw `T=1001 L/R` 仍未证明非零；PC 手控已有运动信号别名，但完整 Nav2 路线执行和 delivery success 仍未完成。
- RViz2/Foxglove 是工程观察工具，不替代 PC 简易发车界面；后续若要远程多人完整 ROS topic 观察，需要保持上位机 Foxglove bridge 启动。
