# Sprint 2026.05.14_23-24 PC Route Debug Console - Side2Side Check

sprint_type: epic

## 用户价值对照

| PRD 目标 | 验收结果 | 证据 |
| --- | --- | --- |
| PC 端开发者/操作员能打开只读 route debug console | 通过，Task A 新增 `pc-tools/route/route_debug_web.py` 与 README | `schema=trashbot.pc_route_debug_console.v1`、HTML/API、`--once-json` drill |
| 展示当前位置、目标点、匹配状态、失败原因和最近任务状态 | 通过，摘要字段覆盖 Objective 3 KR5 | `route_progress`、`keyframe_preflight`、`current_position`、`current_checkpoint`、`target`、`match_status`、`failure`、`recent_task` |
| diagnostics 只暴露 metadata-only summary | 通过，Task B 只接受 schema + boundary 匹配材料，异常和 unsafe copy 保守降级 | `pc_route_debug_console_ref`、`TRASHBOT_PC_ROUTE_DEBUG_CONSOLE`、control boundary false |
| mobile/web 只读展示可用性，不新增控制授权 | 通过，Task C 新增 availability 面板，不读取 PC 文件/raw artifact | Start/Confirm/Cancel gating 未改变，`primary_actions_enabled=false` |
| 不把本机软件证据写成真实路线、HIL 或 delivery success | 通过，所有收口材料标注 `software_proof_docker_pc_route_debug_console_gate`、`not_proven`、`delivery_success=false` | sprint 文档、OKR、进度日志和 required `rg` |

## OKR 映射核对

- Objective 3：满足 KR5 的软件层 PC 关键帧调试页面证据，进度从约 81% 谨慎上调到约 82%。
- Objective 2：recent task / failure / evidence boundary 可被 PC console、diagnostics 和 mobile 只读摘要复盘，进度从约 81% 谨慎上调到约 82%。
- Objective 5：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration，保持约 68%。
- Objective 1：本轮没有真实 WAVE ROVER、串口、UART、Nav2 runtime 或 HIL，保持约 75%。
- Objective 4：手机端只是只读展示 PC debug availability，不是新的手机主路径或真实设备证明，保持约 95%。

## KR 拆解验收

- KR3/O3 fixed route dry-run 支撑项：PC console 可消费本地 JSON status/task 材料，但仍不等于真实 fixed-route 实跑。
- KR5/O3 PC 关键帧调试页面：本轮达到 software proof，页面/API 字段覆盖当前位置、目标点、匹配状态、失败原因和最近任务状态。
- KR5/O2 每次任务可复盘记录：recent task 摘要进入 PC/diagnostics/mobile 只读链路，但仍缺同一 `evidence_ref` 上车复账和真实送达记录。

## 风险和边界

- `software_proof_docker_pc_route_debug_console_gate` 是本机 Docker/local software proof，不是真实 Nav2/fixed-route、真实路线采集或真实机器人运行。
- `not_proven` 必须继续包含 HIL、真实底盘运动、真实串口、dropoff/cancel completion、delivery success 和 Objective 5 外部证明。
- 手机端 availability 面板不可被后续实现误用为控制入口；Start/Confirm/Cancel 仍由原有 readiness/command safety gate 决定。

## 收口结论

Product 验收通过，可以更新 OKR：Objective 2 约 81% -> 约 82%，Objective 3 约 81% -> 约 82%；Objective 1、Objective 4、Objective 5 保持不变。
