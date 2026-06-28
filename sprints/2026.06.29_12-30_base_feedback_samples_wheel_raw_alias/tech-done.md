# sprint_type: micro

## 实际改动

- `/api/robot-control/base/feedback-samples` 新增顶层 wheel raw 只读 alias：
  - `wheel_raw_left`
  - `wheel_raw_right`
  - `wheel_feedback_lr_nonzero_proven`
  - `wheel_feedback_source`
  - `wheel_feedback_plain_hint`
  - `wheel_feedback_next_action`
- 顶层 alias 全部从 `sample_key_values` 派生，避免现场 curl/jq 只能翻嵌套字段才能确认 `wheel raw L/R`。
- `wheel_feedback_plain_hint` 明确说明反馈采样是只读，不是运动命令，也不能单独替代试动、键盘或 Nav2 执行窗口材料。
- 只改只读反馈采样响应合同和测试，不触发底盘 manual、Nav2、自由移动或送达确认。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "base feedback samples expose top-level wheel raw aliases|raw wheel L/R from base feedback samples"`：通过，2 passed。
- `npm --prefix pc-tools/workstation test`：通过，367 passed。
- `npm --prefix pc-tools/workstation run build`：通过，Vite 仍提示现有 chunk 大于 500 kB 的非阻塞 warning。
- `git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/test/catalog.test.ts`：通过。
- 已重启 PC Node 到 `0.0.0.0:7001`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node PID 81728 监听 `*:7001`。
- 只读 live `POST /api/robot-control/base/feedback-samples`：第一次顶层返回 `wheel_raw_left=0`、`wheel_raw_right=0`、`wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_source=vendor_t1001_L_R`，`wheel_feedback_plain_hint` 明确 `wheel raw L/R=0/0` 且“这不是运动命令”；后续同一只读采样返回 `wheel_raw_left=not_observed`、`wheel_raw_right=not_observed`、`t1001_observed_count=0`，说明当前反馈采样有波动；两次均为 `sends_motion_commands=false`、`robot_control_executed=false`。
- 只读 live `GET /api/robot-control/summary`：base 当前读到 `wheel_raw_left=0`、`wheel_raw_right=0`、`lr_nonzero=false`；键盘 next action 仍是勾安全确认后按住方向键连续低速移动；Nav2 仍是上次路线 action 成功但 `wheel raw L/R=0/0` 未非零；`robot_control_executed=false`。

## 剩余风险

- 本轮只补齐只读反馈采样接口的一眼读法；没有执行低速试动、键盘连续手控或 Nav2 重跑，所以仍未证明真实运动窗口内 `wheel raw L/R` 非零；live 只读采样还出现过 `not_observed`，反馈链路本身仍需现场复验。
- 完整目标仍未完成：需要现场安全确认后执行自由移动/键盘/Nav2 实测，并在地图、画面、雷达 overlay 中形成真实当前证据。
