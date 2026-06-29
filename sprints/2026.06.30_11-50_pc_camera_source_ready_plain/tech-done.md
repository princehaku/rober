# 2026.06.30 11:50 PC Camera Source Ready Plain

sprint_type: micro

## 实际改动

- 修正 `pc-tools/workstation/src/server/robotControlSummary.ts`：相机源首帧已观察到但本页共享预览尚未显示缓存帧时，summary 白话改为“相机源首帧已读到；本页共享实时预览还没显示缓存帧”。
- 保持 WYSIWYG 口径：`camera_current_frame_visible=false` 仍表示当前页面没画面，但不再暗示相机源没有首帧。
- 修正 `pc-tools/workstation/src/server/index.ts`：独立 MJPEG status 将 `open_shared_preview` 翻译成中文下一步。
- 补充 catalog 测试，覆盖成功首帧 overlay 与独立 MJPEG status 的中文下一步。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary promotes successful camera first-frame probe overlay over stale source failure"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "workstation camera MJPEG status translates open shared preview action after source first-frame is observed"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- --run`，2 files / 389 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 通过；保留既有 bundle size warning。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `*:7001`。只读 live summary 返回 `camera.status=ready`、`source_readiness=first_frame_observed`、`preview_status=idle_not_started`、`preview_plain_hint=相机源首帧已读到；本页共享实时预览还没显示缓存帧。`；`current_fact_plain` 和 `camera_preview.summary_plain` 同步显示源首帧已读到且本页预览未显示；MJPEG status 返回 `source_diagnosis_next_action_plain=打开共享实时预览；页面会复用同一条上游流。`、`robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC 只读文案；真实页面是否能显示实时预览仍取决于用户浏览器是否打开共享 MJPEG 画面和上车端 MJPEG relay 状态。
