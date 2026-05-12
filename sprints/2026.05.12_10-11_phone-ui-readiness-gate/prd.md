# Sprint 2026.05.12_10-11 Phone UI Readiness Gate - PRD

## 状态

- 阶段：prd
- 创建时间：2026-05-12 10:11 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 目标 Objective：O5 手机体验与低成本量产边界
- 证据边界：`software_proof_docker_local_phone_ui_readiness_gate`

## 1. 用户价值和产品北极星

普通用户只应看到“现在能不能发车、为什么不能、下一步怎么恢复、是否需要人工帮助”。用户不应理解 remote bridge、SQLite、preflight、ACK、ROS topic、串口或硬件参数。

本轮产品目标：形成一个 Docker/local 可验收的 phone UI readiness gate，让正式手机入口从 debug/operator 字段堆叠推进到可读、可操作、可恢复的用户入口。它是 O5 正式手机体验的前置 gate，不是 O6 backend 的又一轮 proof。

## 2. OKR 映射

| Objective / KR | 本轮关系 | 验收口径 |
| --- | --- | --- |
| O5 KR1 手机端最小流程 | 直接推进 | 手机入口聚合连接/状态/发车/异常/恢复路径，不要求用户接触命令行。 |
| O5 KR4 远程诊断最小数据包 | 直接推进 | 手机入口能展示 phone-safe readiness、preflight/backup restore 状态和支持诊断摘要。 |
| O5 KR5 普通用户验收标准 | 直接推进 | 用户看中文优先提示和下一步动作，不看 raw JSON/ROS/串口。 |
| O5 KR7 美观且能直接使用 | 部分推进 | 本轮是 readiness gate，要求 phone-first 首屏和基本视觉层级；不承诺完整正式 app。 |
| O6 KR1/KR6 | 依赖输入 | 消费上一轮 remote command/status/ack、preflight、backup/restore 字段，但不提升 O6 作为主目标。 |

O1/O2/O3/O4 不在本轮主目标内；没有真实硬件、路线、相机、Nav2 或 HIL 证据时不得更新这些 Objective。

## 3. KR 拆解或更新

本轮不直接修改 `OKR.md`，但为后续 O5 提供验收证据：

- O5-KR1-readiness：手机入口可以在本地/Docker 环境显示 remote/local readiness、status stale、command pending、auth failed、cloud unreachable、malformed response。
- O5-KR4-diagnostics：手机入口或 readiness snapshot 可以展示 backup/restore/preflight 的 phone-safe summary、retry hint 和 not-proven boundary。
- O5-KR5-recovery：每类阻塞必须有普通用户下一步提示，例如等待机器人状态、重新登录、稍后重试、联系支持、切换本地 fallback。
- O5-KR7-ui-gate：首屏应聚合主状态、主操作和恢复提示；点击区域、字号、信息层级适合手机浏览器，不把 debug 细节放在主路径。

## 4. 需求范围

### P0 必交付

1. Phone UI readiness snapshot/API 或 operator 手机入口聚合层。
   - 工程 owner 可选择在 `operator_gateway` 页面/API 中实现，也可新增后端聚合 helper；必须复用现有契约。
   - 聚合结果必须覆盖 remote readiness、backup/restore/preflight、delivery command state 和人工可恢复提示。

2. Phone-safe 用户文案。
   - 文案中文优先，允许保留既有英文状态但主恢复提示应能让普通用户理解。
   - 不展示 raw JSON、traceback、ROS topic、串口、baudrate、WAVE ROVER 参数、`/cmd_vel`、bearer token、Authorization header 或云 URL secret。

3. 状态边界标识。
   - 明确 local/Docker proof、preflight blocked、backup/restore drill valid/invalid/not run 均不是真实云、真实 4G、真实送达或 HIL。
   - ACK 只代表 command envelope terminal state，不代表送达成功。

4. 现有 full-stack 验证围栏。
   - 使用真实存在的 unittest 文件名。
   - 不使用会产生 `NO TESTS RAN` 的 `test_*review*py` pattern。

### P1 可选

- 优化 dependency-free operator HTML 的 mobile-first 布局、状态分组、主按钮和触控尺寸。
- 为 readiness snapshot 增加稳定 schema/version，便于后续真实 phone app 复用。
- 增加一个最小本地 smoke 脚本或命令，证明 phone readiness 输出可生成且脱敏。

## 5. 明确不做

- 不交付真实手机原生 app 或生产账号体系。
- 不部署真实云、真实 4G/SIM、公网 HTTPS/TLS、生产 DB/queue、OSS/CDN 实流量、STS 或 rotate。
- 不改 remote relay 的生产能力边界，不把 backup/restore drill 写成真实 disaster recovery。
- 不改 Nav2/fixed-route、SLAM、vision、电梯实景识别、WAVE ROVER、串口、底盘协议或 HIL。
- 不新增 broad regression 或大范围测试，只做 full-stack targeted fence。
- 不更新 `OKR.md`、`docs/product/`、`docs/interfaces/` 或其他 sprint；本轮规划阶段只允许三个 sprint 文件。

## 6. 优先级和验收口径

P0 验收：

- 手机入口或 readiness snapshot 的 happy path 和 blocked path 都能展示普通用户下一步。
- remote readiness 状态至少覆盖 `ok`、`status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response`。
- backup/restore/preflight 状态至少覆盖 not run、blocked/invalid、local valid/pass 但 production not proven。
- collect / confirm_dropoff / cancel 的 command pending/ACK/failed/ignored 语义不与 delivery success 混淆。
- 输出脱敏检查通过，不暴露敏感或硬件字段。
- targeted unittest、py_compile、必要 smoke、scoped diff check 通过。

P1 验收：

- 手机首屏信息层级清晰：主状态、主动作、恢复提示、支持诊断入口分层。
- 主操作路径不超过 3 步：打开入口 -> 确认状态/目标 -> 发车或按提示恢复。
- 触控与文案适合 iPhone/Android 主流浏览器。

## 7. 对应责任 Engineer

- `full-stack-software-engineer`：唯一实现 owner，负责 UI/API 聚合、phone-safe 文案、targeted tests、py_compile、必要 smoke、`tech-done.md` 更新。
- `robot-software-engineer`：仅当 Full-stack 发现接口语义冲突时只读确认 `TrashCollection`、ACK、status 或 diagnostics 合同；默认不改代码。
- `product-okr-owner`：后续验收 owner，负责 side-by-side check、final 和是否更新 O5 完成度。

## 8. 风险、阻塞和证据链

- 当前没有真实硬件，所有结果只能是 Docker/local software proof。
- 手机 UI readiness gate 可以证明普通用户入口形态，但不能证明真实手机网络、真实云、真实 4G、真实送达或 HIL。
- 如果实现只把已有 debug 字段重新排列，不能算 O5 KR7 的有效进展；必须有普通用户主路径和恢复提示。
- 如果测试命令使用不存在的文件或 glob 导致 `NO TESTS RAN`，本轮验收失败。
- 如果输出泄露 raw JSON、token、ROS topic、串口或硬件参数，本轮验收失败。

## 9. 需要创建或更新的 sprint 文档

规划阶段：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现和验收阶段：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
