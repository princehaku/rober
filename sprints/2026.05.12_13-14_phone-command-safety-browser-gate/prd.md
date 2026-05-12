# Sprint 2026.05.12_13-14 Phone Command Safety Browser Gate - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 产品结论：进入 tech-plan；本轮目标是手机首屏命令安全 gate，不是补真实云、真实 4G 或硬件 HIL。

## 背景和问题

O5/O6 当前同为约 38%，是最低 OKR 区间。近期 sprint 已连续补齐 remote relay、auth/degradation、Docker deploy、preflight、SQLite、backup/restore、OSS/CDN manifest 和 phone/API consumption gate，但用户仍无法从手机首屏明确判断哪些操作此刻安全可点。

上一轮把诊断对象引用状态带到了 phone/API，但按钮可操作性仍需要被 readiness 直接约束。否则普通用户可能误以为：

- ACK 出现就代表机器人已经送达成功。
- `remote_ready=true` 就代表真实云/4G/HIL 已经通过。
- manifest ready 就代表真实 OSS/CDN 已经跑通。
- status stale 或 command pending 时仍可继续重复点击 Start/Cancel/Confirm。

这些误解会直接破坏“手机是唯一入口”的产品可信度。

## 用户价值和产品北极星

用户价值：普通手机用户打开首屏后，不需要看工程日志，就能知道当前可执行的下一步、为什么某个按钮不能点、命令是否只是已受理、什么时候需要等待或人工接管。

产品北极星：让低成本 ROS2 垃圾投递机器人通过手机完成可解释、可恢复、可售后的核心任务。手机端必须把不安全或未证明的状态挡在操作前，而不是把工程细节丢给用户。

## OKR 映射

- O5 KR1：手机最小流程的每一步必须对应明确 action permission。
- O5 KR5：用户失败时知道下一步；禁用态和等待态必须有普通用户文案。
- O5 KR7：首屏可交互和手机适配进入 browser/API 最小验收。
- O6 KR1：命令/status/ack 保持云中转控制面契约，不暴露低层控制。
- O6 KR6：远程降级状态要影响手机操作权限，并区分网络问题、认证问题、机器人状态问题和诊断对象问题。

## KR 拆解或更新建议

本轮不直接修改 `OKR.md`，实现和验收通过后建议在 final 阶段考虑：

- O5 小幅上调条件：Start/Confirm/Cancel/Diagnostics 已由 readiness/action permissions 约束，并通过最小 browser/API 围栏。
- O6 小幅上调条件：remote readiness 的 degradation/ACK/status stale 语义被手机操作安全 gate 消费，且 robot compatibility fence 证明 command/status/ack 未退化。
- 不上调条件：只有文档、只有 API 字段无 UI 消费、或 browser/API 围栏不能证明按钮状态。

## 本轮核心抓手

把 `phone_readiness` 的解释能力升级为 command safety gate：

- 允许点：下一步安全、状态新鲜、无 pending ACK、认证通过、诊断引用不阻断。
- 禁止点：等待 robot status、等待 ACK、认证失败、云不可达、响应损坏、诊断引用缺失/损坏/过期、任务需要人工接管。
- 解释清楚：ACK 只是命令处理证据，不是送达成功证据。

## 用户故事

1. 作为普通用户，我打开手机首屏时，希望 Start 只有在小车状态和远程 readiness 允许时才可点。
2. 作为普通用户，我点 Start 后，希望看到“命令已受理/等待小车执行”的状态，而不是误以为任务已完成。
3. 作为普通用户，当状态过期、认证失败或云不可达时，希望页面告诉我等待、重新登录、重试云端或切回本地 fallback。
4. 作为售后同学，我希望 Diagnostics 始终可解释当前阻断原因，但不泄露 token、串口、ROS topic 或硬件参数。

## 范围

### P0 必须做

- 首屏 Start、Confirm dropoff、Cancel、Diagnostics 的 enable/disabled 状态由 API 中的 `phone_readiness`、`action_permissions`、`remote_readiness`、delivery state 和 diagnostics readiness 派生。
- `command_pending` 时禁止重复 Start/Confirm，Cancel 仅在安全且语义明确时可用。
- `status_stale` 时禁止把页面显示为 ready，并提示等待小车上报最新状态。
- `auth_failed` 时提示重新登录或检查 access code，不显示 raw Authorization 信息。
- `cloud_unreachable` 或 `malformed_response` 时提示重试云端或联系支持，不显示 traceback。
- manifest `missing/invalid/stale` 时 Diagnostics 可解释，但主路径不能被渲染成完整 green ready。
- ACK 文案明确：ACK != delivery success；送达成功要继续看任务终态。
- 现有 remote bridge command/status/ack/cursor compatibility fence 必须通过。

### P1 尽量做

- 使用最小 browser smoke 或 HTML snapshot 验证手机窄屏首屏按钮、状态文案和诊断入口不重叠。
- 确认关键按钮最小可点击区域和中文文案在常见手机宽度下可读。

### 不做

- 不实现正式手机 app、账号体系、生产云部署、真实 4G/SIM、真实 OSS upload、CDN origin fetch、STS/受限 AK、生产 DB/queue。
- 不做 Nav2/fixed-route 实跑、WAVE ROVER 串口、T1001 feedback、HIL 或真实送达验收。
- 不修改硬件/vendor 文档和硬件 launch 参数。

## 优先级和验收口径

- P0 通过标准：API/页面在 ready、status stale、command pending、auth failed、cloud unreachable、malformed response、manifest missing/invalid/stale 场景下给出正确按钮状态和用户文案。
- P0 通过标准：ACK 相关文案和状态机不把 command accepted 当作 delivery completed。
- P0 通过标准：Full-stack targeted tests 和 Robot compatibility fence 通过。
- P0 通过标准：敏感字段 redaction 继续覆盖 token、Authorization、AK/SK、root password、serial、baudrate、ROS topic、`/cmd_vel`、硬件参数。
- P1 通过标准：最小 browser/API smoke 给出可复查日志、截图或稳定命令输出。

## 对应责任 Engineer

- `full-stack-software-engineer`：实现 API/UI gate、browser/API 围栏、targeted tests、产品 docs 同步、`tech-done.md`。
- `robot-software-engineer`：运行 remote bridge compatibility fence；如有退化，定位到 command/status/ack/cursor 语义层，不改 UI。
- `product-okr-owner`：验收 PRD 对照、证据边界、final 是否建议更新 O5/O6。

## 风险、阻塞和证据边界

- 证据边界是 `software_proof_docker_phone_command_safety_browser_gate`。
- 本轮没有真实手机设备验收；如果只跑本地浏览器或 API smoke，必须在 final 写清“不是正式手机 app/真实手机验收”。
- 本轮没有真实云、4G、OSS/CDN 实流量和生产账号；不能提升真实生产可用口径。
- 本轮没有硬件；不能提升 O1/HIL，也不能说 WAVE ROVER 已运动或送达成功。
- 如果实现只补测试、不改用户触点，不建议上调 O5/O6。

## 需要创建或更新的 sprint 文档

- 本阶段：`pre_start.md`、`prd.md`、`tech-plan.md`
- 实现阶段：`tech-done.md`
- 验收阶段：`side2side_check.md`
- 收口阶段：`final.md`，并在证据充分后再决定是否更新 `OKR.md`
