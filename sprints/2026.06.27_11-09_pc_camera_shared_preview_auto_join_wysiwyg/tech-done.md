# PC 共享画面自动接入所见即所得

sprint_type: micro

## 实际改动

- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：相机服务 ready/devices loaded 且页面已挂载共享 MJPEG fallback 时，普通首屏实时画面卡显示 `连接中`，提示“正在接入共享实时画面；新页面会共用同一条上游流”，不再误写“未打开”。
- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`当前事实` 在 `source_not_probed/source_selected_not_probed` 且非独占时写明已选中摄像头、共享预览会自动接入、尚未确认真实帧。
- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：共享状态只在尚未看到 MJPEG/video 真实帧时显示“页面正在接入共享预览”；MJPEG `load` 后只显示共享流状态，避免把已出图误说成仍在接入。
- 更新 `pc-tools/workstation/test/App.test.ts`：锁定在线相机自动共享接入、共享状态 fallback、MJPEG `load` 后状态收口，并继续断言不触发 base/manual、free-roam、Nav2 或 camera offer。
- 更新 `docs/product/pc_tools_workstation.md`：同步记录该能力边界。

## 验证结果

- 通过：`npm test -- App.test.ts --testNamePattern "camera readback is online|renders Robot Control V1|shared camera|MJPEG"`；结果 `1 passed`，`7 passed | 156 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅有既有 Vite chunk size warning。
- 通过：`npm test`；结果 `2 passed`，`284 passed`。
- 通过：`git diff --check`。
- 通过：PC Node 继续监听 `0.0.0.0:7001`；live `/api/robot-control/summary` 仍显示相机 `status=source_not_probed`、`devices_status=loaded`、`shared_preview_exclusive_camera_claim=false`、`selected_path=/dev/video1`，普通首屏会按本轮合同显示共享预览自动接入，而不是独占或未打开。

## 剩余风险

- 本轮只修 PC 普通首屏的共享预览状态和 WYSIWYG 文案，不修上车相机无首帧根因。
- 当前 live 仍可能停在 `source_not_probed` 或上游无帧；只有浏览器实际收到 MJPEG `load` 或 video 真实帧后才可作为建图画面 ready。
- Nav2 同窗口 wheel raw L/R 非零、delivery success、真实 free-roam 运动仍未在本轮验证。
