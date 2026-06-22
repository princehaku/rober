# Wheel raw L/R feedback visibility

## sprint_type

micro

## 实际改动

- PC 高级诊断 `采集底盘反馈（高级）` 结果新增 `base feedback raw L/R` 行，直接展示 `latest_L`、`latest_R`、`nonzero_frames`、`proven` 和 `source`。
- `baseFeedbackSamplesSummary` 同步展示 `L/R` 和 `nonzero`，避免现场只看到 `t1001=3/3` 后误解为轮速非零已完成。
- `pc-tools/workstation/test/App.test.ts` 增加 UI 回归，确认 T1001 计数为 3/3 但 L/R=0/0 时仍显示 `proven=false`，且不调用 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md` 同步记录真实复验值和 WAVE ROVER `T=1001 L/R` 判定边界；资料来源为 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON 反馈说明。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，`2 passed (2)`、`105 passed (105)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc`、`vite build`、server `tsc` 均完成。
- `git diff --check`：通过，无 whitespace 输出。
- 真实 PC proxy smoke：`POST /api/robot-control/base/feedback-samples?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，`proxy_status=samples_forwarded`，`remote_http_status=200`，`status=loaded`，`t1001_observed_count=3`，`completed_sample_count=3`，`latest_L=0`，`latest_R=0`，`nonzero_frames=0`，`wheel_feedback_lr_nonzero_proven=false`，`source=vendor_t1001_L_R`，`sends_motion_commands=false`，`robot_control_executed=false`，`dangerous=[]`。

## 剩余风险

- 本轮提升 raw L/R 可见性，但真实 wheel raw L/R 非零仍未达成。
- 当前真实上位机只读反馈可观察到 `T=1001`，但 latest L/R 仍为 `0/0`，不能作为 HIL、物理运动、delivery success 或手动放行证明。
