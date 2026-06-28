# PC 共享实时画面当前事实 WYSIWYG Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：本页 MJPEG 共享预览出图后，顶部 `当前事实` 不再只说“已看到 MJPEG 实时画面”，而是同步显示 `N 个页面共享同一条上游流，不是浏览器独占`；若 status 仍标记独占风险，则显示可能的独占请求。
- `pc-tools/workstation/test/App.test.ts`：扩展共享 MJPEG 出图用例，锁定 `<img>` load 后 `当前事实` 显示 2 个页面共享同一条上游流，并继续覆盖不触发 manual、free-roam 或 Nav2。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录共享实时画面出图后的首屏事实口径和只读边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "shared camera"`，结果 `1 passed (1)`，`3 passed | 201 skipped (204)`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`，`352 passed (352)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有 chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC 普通首屏共享画面事实展示，不触发真实 camera capture、WebRTC offer、Nav2、manual、delivery、free-roam、stop 或 `/cmd_vel`。
- 真机摄像头是否稳定输出首帧、MJPEG relay 是否持续不断流，仍需要继续用上位机/真实浏览器现场证据闭环。
