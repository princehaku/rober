# PC 共享 MJPEG 重试等待所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增本页 MJPEG `<img>` error 后的 retry pending 状态，5 秒换 URL 前在画面卡片、当前事实和共享画面状态中显示“本页共享预览暂时没有出画面，页面会低频自动重试；不是浏览器独占”。
- `pc-tools/workstation/test/App.test.ts`：扩展共享 MJPEG 自动重试测试，覆盖 error 后的画面卡片状态、当前事实、共享画面状态，以及不发送 manual/free-roam/Nav2 控制请求。
- `docs/product/pc_tools_workstation.md`：同步记录本页 MJPEG retry pending 的普通首屏契约。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "retries the shared MJPEG preview after a browser image error without sending motion commands"`，结果 `1 passed | 198 skipped`。
- 通过：`npm test`，结果 `2 passed`、`347 passed`。
- 通过：`npm run lint`，结果 `eslint .` 无报错。
- 通过：`npm run build`，结果 TypeScript 和 Vite build 成功；保留既有 Vite chunk size warning。
- 通过：`git diff --check`，无 whitespace/error 输出。

## 剩余风险

- 本轮只改 PC 端 `<img>` error/retry 的本页呈现，没有连接真实摄像头，也没有新增相机 reader。
- 本轮未触发 WebRTC offer、manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- 工作区已有两份历史 artifact JSON 脏文件，本轮不使用、不修改、不提交。
