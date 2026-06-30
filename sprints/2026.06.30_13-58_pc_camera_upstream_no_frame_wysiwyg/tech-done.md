# PC Camera Upstream No Frame WYSIWYG Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 相机共享预览 DOM evidence 新增 `waitingFirstFrame` 和 `connectedNoFrame`。
  - 普通首屏相机面板、MJPEG 图像和 `plain-camera-current-frame-proof` 暴露 `data-shared-preview-waiting-first-frame` 与 `data-shared-preview-connected-no-frame`。
  - 当共享 MJPEG 上游已经连接但 content-type/首帧未出现时，仍保持 `data-current-frame-visible=false`，状态显示为接入中，避免把黑框或上游连接误当成画面可见。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live-like 用例：`upstream_active=true`、`content_type_loaded=false`、`current_frame_visible=false` 时必须输出等待首帧证据，且不发送任何运动请求。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步相机 WYSIWYG 合同。

## 验证结果

- `npm test -- test/App.test.ts -t "marks shared camera upstream connected but not visible until first MJPEG frame arrives"`：通过，1 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、397 个测试全部通过。
- `npm run lint`：通过，0 个 error；保留既有 4 个 Vue warning。
- `npm run build`：通过，生成 `dist/assets/index-DiljrbNE.js` 与 `dist/assets/index-DCA8Xtd4.css`。
- `git diff --check`：通过。
- 7001 live 验证：
  - 已停止旧 `node` PID `75811`，新 `node` PID `89890` 监听 `*:7001`。
  - `curl http://127.0.0.1:7001/` 返回新资产 `/assets/index-DiljrbNE.js` 和 `/assets/index-DCA8Xtd4.css`。
  - 打包 JS 命中 `data-shared-preview-waiting-first-frame`、`data-shared-preview-connected-no-frame` 和“共享预览正在等待首帧”。
  - `GET /api/robot-control/summary` 当前相机 live 状态为 `shared_preview_client_count=1`、`shared_preview_upstream_active=true`、`shared_preview_content_type_loaded=false`、`shared_preview_cached_frame_loaded=false`，`shared_preview_realtime_plain=共享预览正在等待首帧；首帧出现前不能把黑框当作画面可见。`
- 代码路径确认：首屏 `plain-current-facts` 会在后端 `current_fact_plain` 后追加前端 `plainCurrentCameraFactText()`，该函数已优先处理“上游已连接但未拿到视频边界/首帧”的状态。

## 剩余风险

- 本轮只补 PC Web 只读 DOM 证据，不新开相机 reader、不修复 UVC 无首帧、不发送任何运动命令。
- live 相机首帧仍依赖现场 USB、摄像头输入、格式或供电恢复；该字段只让页面正确表达“已接入共享上游但画面还没可见”。
