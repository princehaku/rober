# PC 相机共享预览白话入口

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 Robot Control summary 的 camera readback 增加 `shared_preview_access_plain` 和 `shared_preview_realtime_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增共享预览白话摘要，把“非独占、同一条上游流、观看页面数、是否已有可见缓存帧”压成两句普通用户可读事实。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：锁定 summary 和前端 fixture 的新增字段。
- `docs/product/pc_tools_workstation.md`：同步记录相机共享预览字段的只读语义和不触发车控边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies"`，结果 `1 passed | 159 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：重启 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，确认 `shared_preview_access_plain=共享预览不是页面独占；谁打开页面都接入同一条上游流，当前 0 个页面观看。`，`shared_preview_realtime_plain` 明确当前没有实时画面且原因是 UVC 未出帧，不是页面独占。

## 剩余风险

- 当前改动只补 PC summary 的相机共享预览可读性；真实画面首帧仍依赖上位机 UVC 输出、USB/供电和 camera service 状态。
