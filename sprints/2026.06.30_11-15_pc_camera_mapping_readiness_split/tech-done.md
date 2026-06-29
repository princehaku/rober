# 2026.06.30 11:15 PC Camera / Mapping Readiness Split

sprint_type: micro

## 实际改动

- 后端 `camera_preview` action card 新增 `camera_source_first_frame_ready`、`camera_source_readiness`、`camera_blocks_mapping_start` 只读证据。
- 画面卡的 `blocks_mapping_start` 从“当前 PC 页面是否绘制预览”改为“相机源首帧是否已证明”，避免多页面或页面刚加载时误挡建图。
- 普通首屏 DOM 同步暴露新的 `data-camera-source-*` / `data-camera-blocks-mapping-start` 属性，并兼容旧 summary 前端派生证据。
- 补充 catalog/App 测试，覆盖“源首帧已证明但本页预览未显示”的场景。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary promotes successful camera first-frame probe overlay over stale source failure"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary reflects camera source first-frame failure in shared preview status"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "keeps camera source first-frame readiness separate from current page preview visibility"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- --run`，2 files / 387 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 通过；保留既有 bundle size warning。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `*:7001`。只读 live summary 返回 `camera_preview.status=not_visible`、`camera_current_frame_visible=false`、`camera_source_first_frame_ready=true`、`camera_source_readiness=first_frame_observed`、`camera_blocks_mapping_start=false`、`camera_preview.blocks_mapping_start=false`；`mapping_start.status=ready`、`mapping_start_ready=true`、`mapping_start_missing_reasons=[]`。

## 剩余风险

- 当前改动只修正 PC Node summary/UI 的只读证据口径；真实建图启动、真实车体运动和真实地图验收仍以现场上位机状态和安全确认链路为准。
