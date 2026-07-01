# 当前卡点共享预览入口

sprint_type: micro

## 实际改动

- `plain-live-camera-recovery-readback` 新增 `plain-live-camera-shared-preview-link` “打开共享预览”链接，直接打开 PC Node 共享 MJPEG relay。
- 链接固定只读，复用 `/api/robot-control/camera/mjpeg` 和当前 `baseUrl`，不启动独占相机、不触发任何 motion/control endpoint。
- 更新 App 测试和产品文档，明确当前卡点即可打开多人共享预览。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，结果 `1 passed | 230 skipped`。
- 通过：`npm run lint`，结果 `eslint .` 无报错。
- 通过：`npm run build`，结果 `tsc` 与 `vite build` 通过；保留既有 chunk size warning。
- 通过：`npm test`，结果 `3 passed` 测试文件、`417 passed` 用例。
- 通过：`git diff --check`，无空白错误。

## 剩余风险

- 本轮只改当前卡点链接和只读 DOM；若硬件仍在 USB 12M full-speed 或无首帧，链接会展示同一真实失败/等待状态，不会凭空生成画面。
