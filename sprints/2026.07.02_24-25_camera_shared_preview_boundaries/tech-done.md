# 共享相机预览只读边界 Micro Sprint

sprint_type: micro

## 实际改动

- 补齐 `GET /api/robot-control/camera/mjpeg/status` 的 `shared_preview_*` 只读边界：共享预览不会启动独占相机、Nav2、manual、keyboard、free-roam、map runtime，不提交 delivery，不执行 stop。
- 补齐 `GET /api/robot-control/summary` 顶层 `camera_shared_preview_*` 同源边界，并同步到普通首屏 `plain-live-closure-summary` DOM。
- 更新 catalog、summary、App 测试和 PC 工作站产品文档，确保现场 curl 与 DOM smoke 都能证明“谁进来都看同一条共享预览，不误触运动链路”。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`（3 files / 429 tests passed）
- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm run build`
- 通过：`cd pc-tools/workstation && npm run lint`

## 剩余风险

- 本轮只验证 PC Node/Vue 合同与测试夹具，不启动真实相机硬件、不打开真实 MJPEG 上游，也不执行任何运动接口。
