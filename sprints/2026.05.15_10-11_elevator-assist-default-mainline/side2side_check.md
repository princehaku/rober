# Sprint 2026.05.15_10-11 Elevator Assist Default Mainline - Side2Side Check

sprint_type: epic

## 1. 用户验收口径对照

| 验收项 | 本轮结果 | 证据 |
| --- | --- | --- |
| 电梯 assisted delivery 不再默认关闭 | 通过 | `task_orchestrator.py` 默认 `elevator_assist_enabled=True`，`autonomous.launch.py` 默认 `true`。 |
| 默认模式仍安全 | 通过 | `elevator_assist_mode=dry_run` 保持默认；task record 写入 `software_proof_docker_elevator_assist_default_mainline_gate`。 |
| 显式关闭有告警和恢复建议 | 通过 | `reason=disabled_by_operator`、warning、`rerun_guidance`、`safe_phone_copy` 被测试覆盖。 |
| 手机端只读解释状态 | 通过 | `mobile/web/app.js` 注入“电梯辅助状态” panel，展示 phase chain、目标楼层、人工协助、失败/接管原因和 not_proven。 |
| 不改变危险操作 gating | 通过 | mobile test 确认 elevator assist panel 不调用 Start/Confirm/Cancel/diagnostics mutating path；`delivery_success=false`、`primary_actions_enabled=false` 固定展示。 |
| 文档同步 | 通过 | `docs/interfaces/ros_contracts.md` 和 `docs/product/mobile_user_flow.md` 已同步工程状态和边界。 |

## 2. 边界声明

本轮只证明 `software_proof_docker_elevator_assist_default_mainline_gate`：

- 不证明真实电梯。
- 不证明真实喇叭/TTS。
- 不证明真实 Nav2/fixed-route 驶入或驶出。
- 不证明 WAVE ROVER、真实串口/UART 或 HIL。
- 不证明真实 dropoff/cancel completion。
- 不证明 delivery success。
- 不证明 Objective 5 external proof，包括真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 或 production app。

## 3. 对照结论

Product 验收通过：本轮把 Objective 2 KR7 的“跨楼层任务默认启用电梯状态链”从默认关闭推进到默认启用 dry-run 主链路，并让 Robot task record / diagnostics 与手机只读面板用同一 evidence boundary 表达。该结论不越界到真实电梯、真实送达或 O5 外部证据。

## 4. 下一步补证

下一轮若继续推进 Objective 2，应从 software proof 进入受控楼宇证据链：同一 `evidence_ref` 下收集真实门状态、楼层确认、人工协助按键记录、Nav2/fixed-route runtime log、task completion、失败恢复记录和 HIL/WAVE ROVER 运行材料。
