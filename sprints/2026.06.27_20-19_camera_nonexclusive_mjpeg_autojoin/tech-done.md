# Camera Nonexclusive MJPEG Autojoin

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当相机首帧失败但诊断显示不是外部独占时，普通首屏优先展示共享 MJPEG 正在自动接入；外部占用仍保持失败提示。
- `pc-tools/workstation/test/App.test.ts`：更新 live 非独占无帧场景回归，确认 MJPEG 入口存在、面板显示连接中、当前事实仍保留无帧/非独占归因。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录非独占无帧时的共享预览口径。

## 验证结果

- `npm test -- test/App.test.ts --testNamePattern "camera|画面|MJPEG|shared preview"`：通过，29 个相关测试通过。
- `npm test`：通过，309 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提示。
- `git diff --check`：通过。
- live 读回 `http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787`：`shared_capture=true`，`exclusive_camera_claim=false`，`source_diagnosis_status=uvc_no_frame_not_exclusive`，`source_diagnosis_not_exclusive=true`；7001 根路径返回 200，静态页面已重建。

## 剩余风险

- 本轮只改 PC 端共享预览展示和自动接入口径，不修复当前真实 UVC 无帧问题；建图 camera ready 仍要求真实首帧或 MJPEG 帧已绘制。
