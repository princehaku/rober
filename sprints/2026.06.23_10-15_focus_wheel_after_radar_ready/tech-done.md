# 雷达运行后聚焦轮速记录

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `刷新雷达` 完成后，如果页面状态判断为 `雷达已运行`，自动把焦点移到 `轮速记录` 面板，帮助现场继续执行低速试动并采集 wheel raw L/R 与 LiDAR delta。该动作只移动焦点，不自动触发 first-jog、manual、keyboard pulse、stop、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：扩展雷达刷新测试，验证刷新后焦点落到 `plain-wheel-record`，并确认没有调用 first-jog 或 manual。
- `docs/product/pc_tools_workstation.md`：同步普通首屏雷达运行后的下一步聚焦规则和安全边界。

## 真实上位机只读证据

- 本轮只读复查显示 `ssh root@192.168.1.11 -p 37878` 可连接。
- `/api/status`：LiDAR `lifecycle_running=false`、`lifecycle_state=stopped`、`latest_scan_proof_fresh=false`、`continuous_scan_status=lifecycle_not_running`。
- `/api/base/feedback-samples/latest`：T1001 可读，但 `latest_pair.left_speed=0.0`、`right_speed=0.0`、`lr_nonzero_observed=false`。
- `/api/delivery/latest`：`delivery_success=false`，仍缺最终确认、operator observed motion/stop 和 structured delivery success。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、137 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，完成 app/server TypeScript 与 Vite production build。
- 通过：`git diff --check`。
- 已恢复 `npm test` 改写的历史 smoke JSON `checked_at` 副作用，提交范围不包含旧 artifacts 噪声。

## 剩余风险

- 本轮只改善雷达运行后的 PC 引导，不证明 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或真实 PC 键盘连续手控。
- 真实 first-jog/manual/Nav2/delivery 操作仍需要现场 operator 显式确认后触发。
