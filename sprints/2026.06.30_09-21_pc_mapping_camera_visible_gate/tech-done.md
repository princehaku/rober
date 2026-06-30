# 建图入口补齐本页画面可见证据

sprint_type: micro

## 实际改动

- 普通首屏 `plain-mapping-start-gate` 新增本页画面 WYSIWYG 证据。
- 建图入口现在区分“相机首帧可用于建图”和“当前 PC 页面已经看到 MJPEG/视频帧”。
- 新增 DOM 字段：`data-camera-current-frame-visible`、`data-camera-current-mjpeg-frame-visible`、`data-camera-current-video-frame-visible`、`data-camera-shared-preview-single-upstream`、`data-camera-shared-preview-client-count`、`data-fixed-shared-preview-endpoint`、`data-fixed-shared-preview-status-endpoint`。
- 同步更新 PC 工作站 README 和产品边界文档。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "points mapping-ready users to start the map recording when only mapping runtime is missing"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "auto connects shared Camera Preview when the page opens and camera source is ready"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，389 passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue newline warnings。
- 通过：`npm run build`，生成 `dist/assets/index-DJgw60-X.css` 和 `dist/assets/index-diDPNnyc.js`；仅 Vite chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮仅改 PC Web 只读仪表、DOM 合同和文档，不包含真实摄像头上车画面、真实多人浏览器访问、真实建图记录或 HIL 验证。
