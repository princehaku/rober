# 2026-06-28 19:05 PC 当前事实共享画面缓存帧

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的画面行新增共享 MJPEG 最近帧缓存状态。
  - 当 `/api/robot-control/camera/mjpeg/status` 已证明 relay 有最近帧缓存，但本页 `<img>` 尚未 load 时，显示“共享流已有最近帧缓存，新页面会先显示最近画面；本页仍在接入实时流”。
  - 该状态不把缓存帧升级成“本页已绘制实时帧”，也不新增相机 reader。
- `pc-tools/workstation/test/App.test.ts`
  - 加强共享 Camera Preview 自动接入测试，锁定缓存帧提示同步进入 `当前事实`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏当前事实对共享 MJPEG 缓存帧的 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "auto connects shared Camera Preview"`
  - 结果：1 个测试文件通过，1 个目标测试通过，196 个测试按过滤跳过。
- 通过：`npm test -- --run test/App.test.ts -t "shared preview auto-join|camera health timeout|source usage is not loaded|renders Robot Control V1"`
  - 结果：1 个测试文件通过，4 个回归测试通过，193 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，345 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实摄像头 HIL 或浏览器人工验收；验证范围限定在 PC 普通首屏只读展示和回归测试。
- 未发送任何 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel` 请求。
