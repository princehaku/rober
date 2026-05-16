# Sprint 2026.05.17_04-05 Route Task Field Retest Drill Console - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `route_task_field_retest_drill_console` 的跨端 software proof：PC gate、Robot diagnostics metadata-only consumer、mobile/web 只读 panel 和相关文档均已由对应 worker 落地并通过围栏验证。证据边界固定为 `software_proof_docker_route_task_field_retest_drill_console_gate`。

本轮不是实机或外部云闭环：不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 dropoff/cancel completion、delivery success、WAVE ROVER、UART、2D LiDAR、ToF、HIL、真实手机/browser、production app 或 Objective 5 external proof。所有 closeout 继续保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和产品北极星

北极星仍是让普通手机用户能把垃圾交给低成本 ROS2 小车，并得到可理解、可追溯、可支持的送达体验。

本轮价值在于把上一轮 `route_task_field_retest_operator_drill` 的命令顺序推进为可读的演练控制台：现场支持可以围绕同一 `evidence_ref` 看到 material pack、result intake、result reconciliation 的 command labels、safe checklist、missing prompts 和 callback checklist。手机端仍只读解释，不暴露 raw artifact、raw JSON、路径、凭证、ROS topic、serial/UART、WAVE ROVER 或控制动作。

## 3. OKR 进展

- Objective 2：约 86% -> 约 87%。field retest operator drill 被推进为 PC / Robot / mobile 共同消费的 drill console，能把门状态、目标楼层、人工协助、dropoff/cancel completion 和 delivery result 的下一步回填清单更稳定地串到同一 `evidence_ref`；但没有真实电梯、真实送达、真实 dropoff/cancel completion 或 delivery success。
- Objective 3：约 86% -> 约 87%。material pack / result intake / result reconciliation 的 command labels、safe checklist、missing prompts 和 callback checklist 已形成 console summary，真实 Nav2/fixed-route runtime log、route completion signal、task record 的现场回填路径更清晰；但没有真实 Nav2/fixed-route 实跑。
- Objective 4：约 97% -> 约 98%。mobile/web 能 phone-safe 展示“现场复测演练控制台”，帮助现场支持理解缺失材料、console status 和边界，且主操作 gating 不变；但没有真实 iPhone/Android browser、production app 或 PWA prompt/user choice。
- Objective 1：保持约 77%。本轮没有真实 WAVE ROVER、UART、2D LiDAR、ToF、HIL-entry、`T=1001` feedback、`/odom`、`/imu/data` 或 `/battery`。
- Objective 5：保持约 66%。Objective 5 仍数值最低，但 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration；本轮不是 Objective 5 external proof。

## 4. 验证结果

Worker 验证已返回：

```text
Autonomy:
py_compile PASS
unittest Ran 5 tests in 0.019s OK
CLI help PASS
required rg PASS
scoped diff check PASS

Robot:
py_compile PASS
unittest Ran 128 tests in 0.181s OK
required rg PASS
scoped diff check PASS

Full-stack:
mobile unittest Ran 30 tests in 0.073s OK
node --check PASS
required rg PASS
scoped diff check PASS
```

Product closeout / 主会话核对：

```text
rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|Objective 2|Objective 3|Objective 4|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #5" sprints/2026.05.17_04-05_route-task-field-retest-drill-console OKR.md docs/process/okr_progress_log.md
PASS: 命中 OKR.md、docs/process/okr_progress_log.md 与本 sprint closeout/planning 文档。

git diff --check -- 本轮 touched files
PASS
```

## 5. 风险和阻塞

- Objective 5 external proof 仍缺：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- Objective 1 / 硬件材料仍缺：真实 WAVE ROVER、UART、2D LiDAR、ToF、HIL-entry、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 和 HIL。
- Objective 2 / Objective 3 仍缺：真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result 和同一 `evidence_ref` 的实机复账。
- Objective 4 仍缺：真实 iPhone/Android browser、production app、真实 PWA prompt/user choice 和真实现场 phone behavior。

## 6. 需要更新的文档

本轮 closeout 已更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

工程 worker 已更新相关文档：`pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。
