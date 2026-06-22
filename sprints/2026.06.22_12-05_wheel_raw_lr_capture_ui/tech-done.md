# sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts` 的 `baseManualMotionKeyValues()` 新增 raw L/R 摘要：
  - `feedback_during_motion_t1001_frame_count`
  - `feedback_after_stop_t1001_frame_count`
  - `wheel_feedback_latest_raw_left`
  - `wheel_feedback_latest_raw_right`
  - 保留 `wheel_feedback_nonzero_frame_count` 与 `wheel_feedback_lr_nonzero_proven`
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 在默认关闭的 `高级诊断 -> 现场点动设置 / 控制边界` 新增 `轮速非零试采（高级）` 按钮，复用 first-jog 固定代理和现场材料 gate；同区块新增 `wheel raw L/R` 行，直接显示 during-motion T1001 帧数、latest L/R、非零帧数和 proven 状态。
- `pc-tools/workstation/test/catalog.test.ts` 新增 PC proxy 测试，模拟上位机 first-jog 返回 during-motion `T=1001` raw `L/R`，断言 PC 响应能暴露 raw L/R 且安全字段仍为 false。
- `docs/product/pc_tools_workstation.md` 同步说明 raw L/R 的来源、边界和失败解释。

## 验证结果

- `cd pc-tools/workstation && npm test` 通过，100 tests。
- `cd pc-tools/workstation && npm run lint` 通过。
- `cd pc-tools/workstation && npm run build` 通过。
- `git diff --check` 通过。
- 重启本机 `npm run api` 后，对真实上位机执行拒绝 smoke：
  - 请求：`POST http://127.0.0.1:8787/api/robot-control/base/first-jog?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - body：`direction=forward, speed=0.08, duration_ms=500, confirm_hil_checklist=true`
  - 返回：HTTP 400、`proxy_status=command_rejected`、`failure_reason=first_jog_preflight_required`、`remote_http_status=null`、`operator_report_preflight.status=blocked`。
  - `remote_motion_key_values=null`、`motion_evidence_gaps` 包含 `motion_command_not_forwarded` 与 `wheel_feedback_lr_nonzero_not_proven`，说明缺现场材料时没有调用远端 `/api/base/manual`。

## 剩余风险

- 当前真实上位机 `/api/base/status` 仍显示 `wheel_feedback_lr_nonzero_proven=false`，且 `/api/operator/report` 缺失；本轮没有在真实底盘上触发 first-jog，以避免在缺现场确认材料时发送运动。
- 该改动让 raw L/R 采集与失败原因更可见，但还没有证明真实 WAVE ROVER `L/R` 非零。
