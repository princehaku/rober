# PC 目标总览

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏新增“目标总览”只读条，按本轮四个目标归并状态：行程/键盘/自由移动、画面/地图/雷达点、发车前确认、自由移动到建图。
- `pc-tools/workstation/src/styles.css`：补充目标总览桌面/移动端布局。
- `pc-tools/workstation/test/App.test.ts`：补充默认首屏断言，确认目标总览不暴露 Nav2、operator report、raw、`/cmd_vel` 等工程词，并验证“画面/地图/雷达点”按钮只聚焦、不发请求。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录目标总览的只读行为边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`。
- 已通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、376 个测试通过。
- 已通过：`npm --prefix pc-tools/workstation run build`；仍有既有 Vite chunk size warning。
- 已通过：PC API 已重启到 `0.0.0.0:7001`，监听 PID `68449`；只读读取 `GET /api/health` 成功，mode 为 `pc_only_readonly_workstation`。
- 已通过：只读读取 `GET /api/robot-control/summary`，live 仍显示本轮目标剩余 6 项；行程/键盘/自由移动可处理，建图未 ready。

## 剩余风险

- 这次只改善首屏目标归并，不调用任何动作接口。
- 真实目标未完成：Nav2 轮速 L/R 非零、键盘连续移动、自由移动、相机首帧、雷达新鲜和建图启动都仍需要现场安全确认后的 HIL 验证。
