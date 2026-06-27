# PC 共享画面缓存帧事实微迭代

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：共享 MJPEG relay 已有最近帧缓存、但本页还没触发 `img load` 时，首屏“当前事实”显示新页面会先看到最近画面并继续接入实时流。
- `pc-tools/workstation/test/App.test.ts`：在共享 camera status pending 用例中锁定上述当前事实，避免把缓存帧说成已出图。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明缓存帧只服务多人共享预览的首屏体验，不创建额外 camera reader，也不触发运动控制。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "keeps shared camera status pending unproven until status polling returns"`，结果 `1 passed | 201 skipped`。
- 发现并修复：首轮完整 `npm test` 发现缓存帧文案覆盖了默认“未确认真实帧”和无帧诊断；已把该文案收窄到 status pending 且 summary 已有缓存帧的窗口，并用相关 5 条测试复验通过。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed`、`350 passed`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；保留既有 Vite chunk size warning，产物构建成功。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修 PC 首屏 WYSIWYG 文案和测试，不访问真实摄像头、不证明真实 MJPEG 像素已经在现场可见，不调用 Nav2、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel`。
