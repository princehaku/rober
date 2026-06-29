# PC 勾确认后可做只读条

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏新增“勾确认后可做”只读条，把图上行程、键盘、自由移动、建图启动分开展示；每行按钮只复用页面内聚焦逻辑，不触发动作接口。
- `pc-tools/workstation/src/styles.css`：补充该只读条的桌面/移动端布局。
- `pc-tools/workstation/test/App.test.ts`：补充默认首屏断言，确认新条不出现 Nav2、operator report、raw、`/cmd_vel` 等工程词，并验证“自由移动”按钮只聚焦安全确认、不发请求。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录最小安全确认后的四类入口和只读行为边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`。
- 已通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、376 个测试通过。
- 已通过：`npm --prefix pc-tools/workstation run build`；仍有既有 Vite chunk size warning。
- 已通过：PC API 已重启到 `0.0.0.0:7001`，监听 PID `57940`；只读读取 `GET /api/health` 成功，mode 为 `pc_only_readonly_workstation`。
- 已通过：只读读取 `GET /api/robot-control/summary`，live 显示图上行程 ready、键盘 ready、自由移动 ready；建图启动仍缺 `camera_first_frame` 和 `lidar_fresh`。

## 剩余风险

- 这次只改善普通首屏最小确认后的动作可读性，不调用 Nav2 执行、键盘启用、自由移动/建图启动、雷达启动或任何底盘接口。
- 真实完成仍依赖现场安全确认后的 HIL 复验：Nav2 需要同窗口轮速 L/R 非零；键盘/自由移动需要现场观察；建图启动仍缺相机首帧和雷达新鲜。
