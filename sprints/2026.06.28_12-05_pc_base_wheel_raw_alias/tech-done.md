# 2026-06-28 12:05 PC base wheel raw alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从 `wheel_feedback_summary.latest_pair.left_speed/right_speed` 派生 `wheel_feedback_latest_raw_left/right`。
  - `readback_summary.base` 同步暴露 `wheel_feedback_latest_raw_left/right`，并兼容未来上位机直接返回 raw alias 的情况。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 在 PC summary contract 的 base readback 中加入可选 `wheel_feedback_latest_raw_left/right` 字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 nested `latest_pair` 和 fresh `/api/base/status` 两条路径，断言 endpoint key_values 与聚合 base summary 都能读到 raw alias。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录该字段只是最新 `T=1001 L/R` 的只读别名，用来对齐普通首屏 `wheel raw L/R` 文案，不新增运动命令或完成证明。

## 验证结果

- `npm test -- test/catalog.test.ts -t "Robot Control summary derives latest wheel L/R from nested feedback summary"`：通过，1 个用例通过、144 个跳过。
- `npm test`：通过，2 个 test file、332 个测试全部通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有前端体积 warning，不影响本轮字段 alias。
- `git diff --check`：通过。
- 重启本机 PC Node 到 `0.0.0.0:7001`：通过，`lsof` 显示 `node` 监听 `TCP *:7001`。
- 只读检查 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，
  `robot_api_connection.status=readable`，`readback_summary.base.wheel_feedback_latest_raw_left=0`，
  `wheel_feedback_latest_raw_right=0`，与 `wheel_feedback_latest_left_speed/right_speed=0/0` 对齐。

## 剩余风险

- 本轮不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`，因此不证明真实 wheel raw L/R 已经非零。
- 当前 live 的底盘反馈仍是 `wheel_feedback_lr_nonzero_proven=false`、`raw L/R=0/0`，需要现场安全确认后通过真实运动窗口复验；该 alias 只让验收脚本可以直接读取 `wheel_feedback_latest_raw_left/right`。
