# 普通首屏启动雷达

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `雷达` 卡片在当前 summary/readback 判断为 `雷达未运行` 时显示 `启动雷达`。该按钮复用既有固定 `radar/start` workstation 代理，只启动 LiDAR lifecycle，不触发底盘、Nav2、delivery 或 `/cmd_vel`。默认雷达已运行时不显示该按钮，`停止雷达` 仍只在高级诊断。
- `pc-tools/workstation/test/App.test.ts`：新增 stopped LiDAR 场景，验证普通首屏显示 `启动雷达`，不显示 `停止雷达` 或工程 endpoint；点击后只调用 `/api/robot-control/radar/start`，不调用 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步普通首屏雷达启动入口和安全边界。

## 真实上位机只读证据

- `ssh root@192.168.1.11 -p 37878` 可连接；上位机 `0.0.0.0:8787` 正在监听。
- 只读 `GET /api/status` 显示 LiDAR lifecycle `running=false`、`state=stopped`，latest scan proof missing。
- 只读 `GET /api/base/feedback-samples/latest` 显示 T1001 反馈可读，但 latest L/R 为 `0.0/0.0`，`lr_nonzero_observed=false`。
- 只读 `GET /api/nav2/goal/execution/latest` 显示历史 goal succeeded 材料存在，但不是本轮新执行。
- 只读 `GET /api/delivery/latest` 显示 `delivery_success=false`，仍缺最终确认、operator observed motion/stop 和 structured delivery success。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、137 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，完成 app/server TypeScript 与 Vite production build。
- 通过：`git diff --check`。
- 已恢复 `npm test` 改写的历史 smoke JSON `checked_at` 副作用，提交范围不包含旧 artifacts 噪声。

## 剩余风险

- 本轮只把当前真实卡点 `雷达未运行` 的启动入口移到普通首屏，不证明 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或真实 PC 键盘连续手控。
- 点击 `启动雷达` 会控制 LiDAR lifecycle；它不是底盘运动，但真实现场仍应观察雷达启动状态后再继续 Nav2/试动流程。
