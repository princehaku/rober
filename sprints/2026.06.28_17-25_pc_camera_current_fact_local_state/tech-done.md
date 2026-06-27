# 2026-06-28 17:25 PC 画面当前事实本地状态同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的画面行优先消费本地相机会话状态。
  - 覆盖检查当前画面 pending、关闭实时画面 pending、MJPEG 已绘制、首帧探针偏暗、WebRTC 正在打开、streaming 但浏览器尚未绘出第一帧等状态。
  - 该改动只调整只读展示，不新增 camera probe、MJPEG、WebRTC、manual、keyboard、Nav2、delivery、free-roam 或 `/cmd_vel` 请求。
- `pc-tools/workstation/test/App.test.ts`
  - 在普通首屏记录当前画面 pending 测试中，锁定 `当前事实` 同步显示“正在检查当前画面”。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首屏画面事实行 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "records the current camera frame from the plain first screen without sending motion"`
  - 结果：1 个测试文件通过，1 个目标测试通过，191 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，339 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实相机或真实小车 HIL；变更限定在 PC 首屏只读展示，不作为真实画面可用或真实运动成功证明。
- 未发送任何真实 camera probe、MJPEG、WebRTC、manual、keyboard、Nav2、delivery、free-roam、base stop 或 `/cmd_vel` 请求；真实画面和真实小车状态仍需现场按安全流程验收。
