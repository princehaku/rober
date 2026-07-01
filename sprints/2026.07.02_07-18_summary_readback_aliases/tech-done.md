# Summary Readback Aliases

sprint_type: micro

## 实际改动

- 补齐 PC `GET /api/robot-control/summary` 顶层现场复验别名：`wheel_rerun_acceptance_endpoints`、
  `wheel_rerun_next_action_plain`、`wheel_rerun_acceptance_plain`、
  `keyboard_continuous_post_hold_feedback_readback_required` 和
  `keyboard_continuous_post_hold_summary_refresh_required`，避免脚本读取轮速复验和键盘按住后读回合同时拿到 `null`。
- 同步更新 TypeScript 合同、单测和 `docs/product/pc_tools_workstation.md`。PC 地图显示口径继续保持：
  普通用户优先用 `/map` 大屏，工程调试才使用 RViz2 或 Foxglove。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：通过，3 个测试文件、428 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 large chunk 提醒。
- `git diff --check`：通过。
- 已重启 PC Node，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` PID 6330 监听 `TCP *:7001`。
- 只读 smoke `GET http://127.0.0.1:7001/api/robot-control/summary`：顶层返回
  `map_display_primary_url=/map`、RViz2 launch 命令、Foxglove Web URL、轮速复验验收端点、轮速复验白话动作/验收口径，
  以及键盘按住后 feedback/summary 读回 required=true。
- `/map` HTTP smoke：`200 text/html; charset=utf-8`。

## 剩余风险

- 本轮没有新的现场安全确认，因此没有执行 Nav2、键盘 manual、free-roam、delivery complete、stop 或 `/cmd_vel`；
  wheel raw L/R 非零和键盘实车连续控制仍需要 CEO 现场确认安全后再跑。
- 摄像头首帧仍受上车 USB/UVC 现场问题影响，本轮只处理 PC summary 合同和地图入口说明。
