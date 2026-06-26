# PC Free Roam Move Independent Of Sensors

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `扫地式建图` 的开始记录门禁不再要求摄像头首帧或雷达 fresh；安全确认、连接和地图刷新状态满足后即可开始记录。
- 同步普通用户文案：传感器未 ready 时显示 `可移动`，提示本轮可低速移动但只能按移动练习处理；摄像头和雷达都 ready 时才显示 `可建图`。
- 修改 `pc-tools/workstation/test/App.test.ts`：更新摄像头无首帧、相机源未证明、雷达 stale 三类用例，锁定“可移动但不等于可建图”的行为，并确认开始记录不会直接发送 base manual、Nav2、delivery 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md`：记录 2026-06-26 23:05 起的产品边界，说明移动不依赖摄像头/雷达，建图验收质量才依赖二者 ready。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts`：通过，`141 passed`。
- `cd pc-tools/workstation && npm run build`：通过，仅保留既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮验证是 PC 前端和 Node 代理层行为验证，没有真实上车 HIL；真实底盘 `T=1001` 轮速 L/R 非零仍需要现场低速运动复测。
- 摄像头现场仍是 `/dev/video1` 可打开但无首帧输出的硬件/输入问题；本轮不把该问题作为移动硬门禁，但它仍会阻止本轮被验收为高质量建图。
- Nav2 完整路线执行已有 PC summary 展示证据，但真实路线再次发车仍需要现场安全确认、定位 TF 链和上车端 preflight 通过。
