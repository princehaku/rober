# Wheel Raw L/R Progress Summary Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `wheelRawLrProgressSummary`，把 wheel raw L/R 证据分成三类展示：
    - 静态 `T=1001` 反馈链路已通但未发送运动命令，不能证明 L/R 非零。
    - manual/first-jog 被 operator report preflight 挡住时，直接显示缺失字段和 report 状态。
    - manual/first-jog 已有 `remote_motion_key_values` 时，优先展示 during-motion T1001 帧数、raw L/R 和非零证明状态。
  - 高级点动区新增 `wheel raw L/R progress` 行，减少现场把静态反馈误判成运动轮速证明的风险。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展静态底盘反馈测试，断言 `L/R=0/0` 场景显示 `static T1001 feedback only` 和下一步操作提示。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `wheel raw L/R progress` 的证据边界。

## 采用资料来源

- `docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER UART 为 newline-delimited JSON。
  - `{"T":130}` 是 `CMD_BASE_FEEDBACK`。
  - `T=1001` 的 `L/R` 是项目采用的 raw wheel feedback 字段。

## 真实状态核对

- SSH 上位机 `root@192.168.1.11 -p 37878` 本轮可连接，主机名为 `op-z3-b6.home`。
- PC proxy 调用 `POST /api/robot-control/base/feedback-samples?baseUrl=http://192.168.1.11:8787` 成功返回：
  - `t1001_observed_count=3`
  - `completed_sample_count=3`
  - `wheel_feedback_latest_left_speed=0`
  - `wheel_feedback_latest_right_speed=0`
  - `wheel_feedback_nonzero_frame_count=0`
  - `wheel_feedback_lr_nonzero_proven=false`
  - `sends_motion_commands=false`
- 因此当前只能证明反馈链路可读，仍不能证明 wheel raw L/R 非零。

## 验证结果

- `npm test`
  - 通过：`Test Files 2 passed (2)`，`Tests 110 passed (110)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。

## 剩余风险

- 本轮没有执行真实 first-jog/manual 运动，原因是当前上位机 latest operator report 是 delivery draft，`operator_present=false`，会挡住 first-jog/manual preflight。
- wheel raw L/R 非零仍未完成；下一步需要现场恢复 first-jog 材料并在操作者可急停的条件下执行轮速非零试采。
- delivery success 仍不能宣称完成。
