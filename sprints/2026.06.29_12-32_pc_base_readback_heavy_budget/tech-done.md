# PC Base Readback Heavy Budget

sprint_type: micro

## 实际改动

- 将 `pc-tools/workstation/src/server/robotControlSummary.ts` 中 `/api/base/status` 与 `/api/base/feedback-samples/latest` 的只读预算从 4s 提升到 8s。
- 更新 `pc-tools/workstation/test/catalog.test.ts`，把 summary route 的慢 base readback 回归用例提高到 4.5s，确保合法慢读不会再被误报为 `fetch_timeout_4000ms`。
- 更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，说明该变化只扩大固定 GET readback 等待窗口，不开放任何控制能力。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "slow base readback|base readback|wheel raw|Nav2"` 通过：`32 passed | 131 skipped`。
- `npm --prefix pc-tools/workstation test` 通过：`2 files / 378 tests passed`。
- `npm --prefix pc-tools/workstation run build` 通过；仅保留既有 Vite chunk-size warning。
- PC API 已重启到 `0.0.0.0:7001`，当前监听 PID 为 `41991`。
- 远端只读复核：`ssh root@192.168.1.11 -p 37878` 下 `ss -ltnp` 继续显示 `0.0.0.0:8787` 与 `0.0.0.0:8088` 监听，未见 `7071`。
- 直连上车端 `/api/base/status` 和 `/api/base/feedback-samples/latest` 均约 3.6s 返回，说明 4s 窗口在并发 summary 下存在误报风险。
- `GET http://127.0.0.1:7001/api/robot-control/summary` 默认返回 `base.status=loaded`、`current_feedback_read_status=t1001_observed`、`wheel_raw_left=0`、`wheel_raw_right=0`；`robot_api_connection.blocked_reasons` 不再包含 `base_status:fetch_timeout_4000ms` 或 `base_feedback_samples_latest:fetch_timeout_4000ms`。
- 同一只读 summary 仍显示 Nav2 最近结果为 `goal_succeeded_wheel_feedback_not_proven`，下一步为现场安全确认后用 ROS 模式重跑图上路线并在同窗口确认 wheel L/R 非零。

## 剩余风险

- 本轮只改善 PC summary 的只读底盘反馈读数窗口，不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 如果上车端 base readback 本身超过 8s 或串口被阻塞，PC 仍会如实显示 fetch timeout；真实运动闭环仍需现场安全确认后重跑并验证 wheel L/R 非零。
- live summary 仍有 `/api/status` 8s timeout，当前不影响 base/Nav2/free-roam/camera 分项读数；后续若总状态聚合仍不稳定，可单独优化 `/api/status` 聚合预算或降级展示策略。
