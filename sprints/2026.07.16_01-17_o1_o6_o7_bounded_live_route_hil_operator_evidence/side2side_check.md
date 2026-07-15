# Side-to-side Check - Phase 0 授权边界

## 验收对象

对照本 sprint 的 PRD 与 Tech Plan，本轮只验收“是否正确停在 explicit live-motion authorization gate”，不验收路线执行、HIL、operator acceptance 或 O6/O7 消费。

## 对照结果

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 避免连续消费 O5 provider blocker | 通过 | `pre_start.md` 与 `tech-plan.md` 明确 O5 约 85% 但两轮后暂停 |
| 选择新的 mission-grade 证据类别 | 通过（计划） | bounded `NavigateToPose` + pre/post stop + same-window `T=1001` + operator evidence |
| SSH 信息不解释为运动授权 | 通过 | PRD/Plan 明确 `authorization_gate=false` |
| 未授权不派 Engineering | 通过 | 无 Algorithm/Hardware/Full-stack 产品改动或 live invocation |
| Owner、文件范围、验收命令清晰 | 通过 | `tech-plan.md` 分阶段列出三类 owner 与 scoped commands |
| Vendor 事实有本地来源 | 通过 | 采用 `docs/vendor/VENDOR_INDEX.md`、`json_cmd.h` 与 vendor feedback tutorial；未新增串口/波特率/速度映射假设 |
| Epic 前置三文档完整 | 通过 | `pre_start.md`、`prd.md`、`tech-plan.md` 均已落盘 |
| Product agent 实际落盘 | 未通过 | 两次规划与一次 closeout follow-up 均停在业务文件/命令前 |
| 工程或 live 目标完成 | 未通过/未开始 | 缺 fresh explicit authorization，按安全边界禁止执行 |

## Product acceptance

接受本轮为 `planning_blocked_pending_explicit_live_motion_authorization` 的诚实收口；拒绝把计划、anchor check、SSH 地址或 agent 尝试记为 OKR progress。O5 约 `85%`、O6/O7 各约 `93%`、O1 约 `94%` 全部保持，KR 不归档。

固定事实：

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `okr_credit=false`

## 未完成与风险

未获得 operator 在场、路线清空、stop ready 和 exactly one live goal 的授权；未验证 SSH、ROS、Nav2、底盘反馈或 stop endpoint 当前状态。子 agent 业务执行通道仍复现 `subagent_runtime_orchestration_timeout_before_business_file_or_command_execution`。下一轮必须先由 CEO/operator 给出精确授权；否则继续保持 blocked，不转去 support-only 替代品。
