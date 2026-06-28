# PC 首屏显示相机共享预览事实

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏相机卡片新增 `共享预览事实` 行，直接显示 summary 中的共享入口与实时可见性白话结论。
- `pc-tools/workstation/test/App.test.ts`：补充首屏 DOM 断言，锁定普通用户能看到“共享预览不是页面独占、谁打开页面都接入同一条上游流”。
- `docs/product/pc_tools_workstation.md`：同步记录首屏消费新增相机 summary 字段的只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "camera"`，结果 `32 passed | 183 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：重启 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，确认 `shared_preview_access_plain` 和 `shared_preview_realtime_plain` live 返回；普通首屏 DOM 由测试锁定 `robot-camera-shared-preview-readback` 会显示共享预览事实。

## 剩余风险

- 当前改动只把已有相机共享预览 summary 展示到普通首屏；真实画面首帧仍取决于上位机 UVC 输出、USB/供电和 camera service。
