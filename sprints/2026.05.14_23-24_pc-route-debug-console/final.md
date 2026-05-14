# Sprint 2026.05.14_23-24 PC Route Debug Console - Final

sprint_type: epic

## 收口结论

本轮完成 `software_proof_docker_pc_route_debug_console_gate`。PC route debug console 已从 onboard 调试入口推进到 `pc-tools/route/` 的独立只读工具，并把可用性摘要以 metadata-only 方式接入 diagnostics 与 mobile/web。

这是 Objective 3 KR5 的软件层进展，也增强了 Objective 2 的任务复盘可读性；它不是真实 Nav2/fixed-route、真实路线采集、HIL、delivery success 或 Objective 5 真实外部证明。

## 用户价值

现场操作员和开发者现在可以在 PC 上用只读页面/API 查看固定路线关键状态：当前位置、当前 checkpoint、目标点、匹配状态、失败原因、关键帧预检和最近任务状态。普通手机用户只看到 PC route debug console availability，不需要接触 raw JSON、PC 文件或 ROS2 细节，也不会获得新的控制入口。

## OKR 更新

- Objective 2：约 81% -> 约 82%。理由：recent task、失败原因、`not_proven` 和 `delivery_success=false` 已能通过 PC console、diagnostics 与 mobile 只读摘要被同一口径复盘。
- Objective 3：约 81% -> 约 82%。理由：PC 关键帧调试页面/API 覆盖 `route_progress`、`keyframe_preflight`、`current_position`、`current_checkpoint`、`target`、`match_status`、`failure` 和 `recent_task`。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration。
- Objective 1：保持约 75%。本轮没有真实 WAVE ROVER、串口/UART、Nav2 runtime、真实底盘运动或 HIL。
- Objective 4：保持约 95%。手机端只是展示 PC debug availability，不构成新的真实手机设备/browser 或 production app 证明。

## 责任 Engineer 和交付

- Task A `autonomy-engineer`：新增 `pc-tools/route/route_debug_web.py`、`pc-tools/route/test_route_debug_web.py`、`pc-tools/route/README.md`，更新 `pc-tools/README.md` 与 `docs/navigation/fixed_route_workflow.md`。
- Task B `robot-software-engineer`：更新 `operator_gateway_diagnostics.py`、`test_operator_gateway_diagnostics.py`、`docs/interfaces/ros_contracts.md`，支持 `pc_route_debug_console_ref` 与 `TRASHBOT_PC_ROUTE_DEBUG_CONSOLE`。
- Task C `full-stack-software-engineer`：更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、fixture、mobile entrypoint test 与 `docs/product/mobile_user_flow.md`，新增只读 PC route debug availability 面板。
- Product closeout：更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 验收结果

工程 worker 验证摘要：

- Task A：py_compile pass；`test_route_debug_web.py` `Ran 5 tests OK`；`--help` pass；`--once-json` 临时 drill pass；required `rg` pass；diff check pass。
- Task B：py_compile pass；diagnostics unittest `Ran 53 tests OK`；required `rg` pass；diff check pass。
- Task C：mobile unittest `Ran 4 tests OK`；py_compile pass；`node --check mobile/web/app.js` pass；required `rg` pass；diff check pass。

Product 收口验收：

- `rg` 覆盖 OKR、进度日志和 sprint 收口文档中的 sprint id、boundary、Objective 2/3/5、`pc_route_debug_console`、`not_proven`、delivery success、HIL、真实公网和本机 Docker 口径。
- `rg` 覆盖工程文档与实现范围中的 `pc_route_debug_console`、`software_proof_docker_pc_route_debug_console_gate`、Objective 2/3、`not_proven`、delivery success 和 HIL。
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_23-24_pc-route-debug-console/tech-done.md sprints/2026.05.14_23-24_pc-route-debug-console/side2side_check.md sprints/2026.05.14_23-24_pc-route-debug-console/final.md`：pass。

## 风险和未完成事项

- 仍缺真实 Nav2/fixed-route 实跑、真实路线采集、关键帧实景证据和同一 `evidence_ref` 上车复账。
- 仍缺 WAVE ROVER、真实串口/UART、HIL、真实底盘运动、dropoff/cancel completion 和 delivery success。
- 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 手机端只读 availability 面板不能替代 PC console，也不能被当作真实手机设备/browser 或 production app 验收。

## 下一步

如果没有真实 Objective 5 外部材料，下一轮不要继续叠加本地 O5 metadata。更有价值的推进方向是 Objective 2/3：用真实 Nav2/fixed-route 或同一 `evidence_ref` 上车复账材料，把本轮 PC console 的 software proof 连接到真实路线/任务证据。
