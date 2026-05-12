# Sprint 2026.05.12_14-15 Remote Network Recovery Drill - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主目标：O6 `software_proof_docker_network_recovery_drill`
- 范围边界：只做 Docker/local 软件证明；不声明真实云、真实 4G/SIM、真实手机设备、Nav2/fixed-route、WAVE ROVER 或 HIL

## 产品问题

13-14 已经让手机按钮根据 command safety gate 决定能否点击，但用户仍缺一个更关键的保障：当远程控制面断网、恢复或 ACK 失败时，系统能否证明自己没有误推进命令 cursor、没有持久化一个未被云端确认的 terminal cursor、没有触发本地 action，并能把问题解释成普通用户可理解的恢复状态。

如果没有这层 proof，手机端后续即使接入真实 4G，也可能在最危险的状态下给出误导：用户以为命令已处理，机器人侧其实没有可靠 ACK；或 robot bridge 以为 terminal ACK 已落云，重启后跳过了应该重试的命令。

## 用户价值

- 用户知道当前是“网络恢复演练未通过/已过期/需要重试”，而不是误以为机器人失败或任务成功。
- 支持人员能拿到一个脱敏 artifact，区分 relay 网络问题、ACK post failure、status stale、auth failed 和 malformed response。
- 机器人侧在云不可达或 ACK 未落云时保持保守行为，避免重复执行、漏执行或错误推进 cursor。

## 产品北极星

正式 4G 链路是：

```text
phone web/app -> cloud HTTPS API -> robot remote_bridge outbound polling -> ROS2 behavior
```

本轮只推进这条链路里的“弱网/断网恢复语义”软件证明。手机仍只是普通用户入口；relay 和 bridge 必须优先保证不可确认时不推进状态，而不是追求 happy path 更顺滑。

## OKR 映射

### Objective 6：4G 云中转 + OSS/CDN 数据通路产品化

- KR1：command/status/ack 语义继续按 `trashbot.remote.v1` 保持幂等、ACK 和 outbound polling 边界。
- KR5：凭证、错误和 artifact 必须保持脱敏，不泄露 token、Authorization、OSS secret 或内部路径。
- KR6：本轮主攻 4G 中断类 graceful degradation 的 Docker/local software proof，输出 network recovery drill artifact 和 phone-safe 恢复摘要。

建议本轮成功后 O6 只做保守小幅上调，原因是它仍不是真实云/4G 证据。

### Objective 5：手机体验与量产边界

- 只作为支撑：phone readiness 消费 network recovery summary，帮助普通用户理解“网络恢复演练状态”。
- 不作为主目标：本轮没有真实手机设备/浏览器验收，也不新增正式手机 app。

### O1/O2/O3/O4

不参与本轮 KR 上调。无真实串口、无 WAVE ROVER feedback、无 Nav2/fixed-route 实跑、无相机实景证据。

## KR 拆解

KR-A：relay network recovery drill

- 可在 Docker/local 环境制造或模拟 cloud unreachable、relay restart/recovery、ACK post failure、status stale。
- 输出 artifact，包含 schema、schema_version、evidence_boundary、steps、cursor_invariant、phone_safe_summary、retry_hint、not_proven、updated_at/checksum。
- Artifact 不包含 bearer token、Authorization header、OSS secret、AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

KR-B：preflight/diagnostics consumption

- Preflight 能消费 network recovery artifact。
- Missing、invalid、stale 或 failed artifact 必须保持 blocked/warning，不显示绿色 ready。
- Diagnostics/phone readiness 只输出 phone-safe summary，不返回 full artifact 或内部路径。

KR-C：remote_bridge compatibility fence

- remote_bridge 在 cloud unreachable、auth failed、malformed command/status/ACK response、ACK post failure 时不触发本地 action。
- ACK post failure 不推进内存 cursor，不写 terminal cursor state。
- 恢复后同一 command 仍可重试，且 terminal ACK 成功后才允许持久化 cursor。

KR-D：文档和证据边界

- `docs/product/remote_4g_mvp.md` 和 `docs/product/cloud_4g_infrastructure.md` 在实现阶段必须同步 network recovery drill 口径。
- Sprint closure 必须明确 `software_proof_docker_network_recovery_drill` 不等于真实 4G、真实云、真实送达或 HIL。

## 本轮需要做什么

1. `full-stack-software-engineer` 实现 relay 侧 drill 和 artifact。
2. `full-stack-software-engineer` 接入 preflight/diagnostics/phone-safe summary。
3. `robot-software-engineer` 补 remote_bridge command/status/ack/cursor compatibility fence。
4. `product-okr-owner` 在执行后验收 artifact 字段、证据边界、phone-safe 文案和 OKR 更新建议。

## 优先级和验收口径

P0 验收：

- 有一条命令可以在 Docker/local 跑出 network recovery drill artifact。
- Artifact 明确 `evidence_boundary=software_proof_docker_network_recovery_drill`。
- Preflight/diagnostics 能消费 artifact，且 missing/invalid/stale/failed 均不 green。
- Robot compatibility fence 证明 ACK 失败不推进 cursor、不触发本地 action。
- Targeted tests、py_compile、Docker/local smoke 和 scoped `git diff --check` 通过。

P1 验收：

- Phone-safe summary 在 `/api/status` 或 `/api/diagnostics` 中可被 operator/phone readiness 消费。
- 用户文案区分“网络问题”“恢复演练未通过/已过期”“需要重新执行演练”。

不验收：

- 真实 HTTPS/TLS、公网入口、4G/SIM、production DB/queue、多实例一致性、真实 OSS upload、CDN origin fetch、正式手机 app、真实手机设备截图、WAVE ROVER、HIL、真实垃圾送达。

## 责任 Engineer

- 主责：`full-stack-software-engineer`
- 兼容性主责：`robot-software-engineer`
- 产品验收：`product-okr-owner`
- 不参与本轮实现：`hardware-engineer`、`autonomy-engineer`

## 风险、阻塞和证据链

- 当前本机只有 Docker，无真实 4G/SIM；最终只能形成 software proof。
- 若 artifact 只证明 relay 自身而没有 remote_bridge compatibility fence，不能算 P0 完成。
- 若 phone-safe summary 泄露内部路径、token、ROS topic、串口或 `/cmd_vel`，必须阻断验收。
- 若实现只新增 UI 文案而没有可执行 drill、artifact 和 compatibility fence，不能提升 O6。
- 若测试范围扩散成大回归，违背“测试只做围栏”；本轮只接受目标文件、目标 unittest、py_compile、Docker/local smoke 和 scoped diff check。
