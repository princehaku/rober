# PC 下一步意图分流

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏新增“下一步选一个”分流条，提供 `先动车`、`跑行程`、`去建图`、`补画面/雷达` 四个入口；每个入口只按当前 summary 显示短状态并聚焦到已有控件。
- `pc-tools/workstation/src/styles.css`：补充分流条桌面/移动端布局。
- `pc-tools/workstation/test/App.test.ts`：补充默认首屏断言，确认分流条不暴露 Nav2、operator report、raw、`/cmd_vel` 等工程词，并验证“跑行程”按钮只聚焦行程安全确认、不发请求。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录分流条的只读行为边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`。
- 已通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、376 个测试通过。
- 已通过：`npm --prefix pc-tools/workstation run build`；仍有既有 Vite chunk size warning。
- 已通过：PC API 已重启到 `0.0.0.0:7001`，监听 PID `63514`；只读读取 `GET /api/health` 成功，mode 为 `pc_only_readonly_workstation`。
- 已通过：只读读取 `GET /api/robot-control/summary`，live 显示 `先动车` 和 `跑行程` 可处理，`去建图` 仍缺 `camera_first_frame` 和 `lidar_fresh`。

## 剩余风险

- 这次只改善普通用户下一步选择，不调用任何动作接口。
- 真实闭环仍需现场安全确认后执行：Nav2 轮速 L/R 非零、键盘连续移动、自由移动、相机首帧、雷达新鲜和建图启动仍未完成 HIL 收口。
