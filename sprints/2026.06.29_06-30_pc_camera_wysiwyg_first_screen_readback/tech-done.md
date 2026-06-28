# PC Camera WYSIWYG First Screen Readback Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- 普通首屏实时画面卡片新增 `画面事实` 行，直接消费 `readback_summary.camera.camera_wysiwyg_status_plain/camera_wysiwyg_next_action_plain`。
- 新增 App 测试断言，确保默认首屏能直接看到后端 WYSIWYG 画面事实，而不是只看到本页浏览器状态或共享预览合同。
- 普通首屏展示层把后端 `画面未可见/画面可见` 转写成 `画面未显示/已经看到画面`，避免普通测试和用户误读成“已经可见”。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录该变化只展示只读 summary，不新开相机上游、不触发控制命令。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`，1 passed，214 skipped。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1|shared preview auto-join|waiting state"`，3 passed，212 skipped。
- 通过：`npm --prefix pc-tools/workstation run build`，Vite build 成功；仅保留既有 chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部 passed。
- 通过：PC API 已重启到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`。
- 通过：只读读取 `http://127.0.0.1:7001/api/robot-control/summary`，`readback_summary.camera` 返回 `status=source_first_frame_failed`、`camera_wysiwyg_status_plain=画面未可见：不是页面独占：USB Composite Device: DV20 USB  (usb-5310000.usb-1) 当前没人占用，但 UVC 设备没有输出视频帧；检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。`、`camera_wysiwyg_next_action_plain=检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`。

## 剩余风险

- 当前改动只把 camera WYSIWYG readback 接到普通首屏，不会打开相机、重启 camera service、调用 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- live 画面仍取决于上车端 UVC 是否实际输出帧；本轮只让“没出帧不是页面独占”的事实更直接可见。
