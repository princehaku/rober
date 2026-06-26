# PC 共享画面非独占失败口径

## sprint_type

micro

## 实际改动

- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `共享画面` 状态直接说明 `exclusive_camera_claim=false` 时不是浏览器独占，而是多个页面共享同一条上游 MJPEG relay。
- 将共享预览 `camera_mjpeg_proxy_failed`、HTTP 502/503 翻译为“上游没有返回可用画面，通常是相机无帧或相机后端不可用”，避免普通用户只看到工程 token。
- 更新 `pc-tools/workstation/test/App.test.ts`：在 live `not_in_use + capture_read_returned_false` 场景中同时锁定共享预览 503 文案，并确认普通首屏不泄露 `camera_mjpeg_proxy_failed`，也不触发 manual 或 free-roam start。
- 更新 `docs/product/pc_tools_workstation.md`：记录 2026-06-27 起共享画面非独占与 502/503 无帧口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "explains a live not-in-use camera first-frame failure"`，结果 `1 passed | 141 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts`，结果 `142 passed`。
- 通过：`git diff --check`，无 whitespace error 输出。

## 剩余风险

- 本轮只改善 PC 画面所见即所得解释，不恢复真实 DV20 首帧。
- 真实上位机仍需处理摄像头输入源、采集卡模式、USB 线/供电或更换 known-good UVC；PC 不造假帧，也不把无帧状态升级为建图 ready。
