# Sprint 2026.05.12_03-04 Remote Cloud Persistence And Phone Readiness - PRD

## 状态

- 阶段：prd
- 时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- 支撑 Objective：O5 手机用户体验与量产边界
- 验收边界：Docker-only software proof；不声明真实云、真实 4G、真实硬件或真实送达闭环

## 1. 用户价值和产品北极星

普通用户只用手机就能知道“小车远程控制链路现在能不能用、上一条命令有没有被机器人处理、如果没处理该等还是该重试”。这服务于 O6 的 4G 云中转北极星：手机和小车不在同一 WiFi 时，通过云端控制面完成命令、状态和 ACK 回传。

本轮不追求视觉 UI 包装，而是补产品化控制面的可靠性底座：队列可恢复、cursor 可解释、status 可读、鉴权边界清楚。

## 2. OKR 推荐

### 推荐 1：首选深入 O6 remote cloud persistence/recovery

- 证据：`OKR.md` 最新快照显示 O6 约 12%，低于 O5 约 30% 和 O1/O2/O3/O4。
- 证据：`2026.05.12_02-03_remote-4g-command-loop/final.md` 明确剩余风险包括真实云前的持久化队列、跨重启 cursor、生产鉴权、弱网/断网恢复。
- 证据：`docs/product/remote_4g_mvp.md` 已有 command/status/ack API contract，但 local mock cloud 当前仍是本地开发控制面，未形成持久化恢复语义。
- 可执行抓手：本轮在 mock cloud 层增加文件或目录型持久化队列 contract，在 `remote_bridge` 增加 cursor/status recovery 边界，并用 targeted tests + Docker-only smoke 证明重启后不会重复错取或丢失命令。

### 推荐 2：同步带动 O5 phone-readable readiness/status

- 证据：`OKR.md` 最新快照显示 O5 约 30%，缺正式手机 UI/普通用户体验。
- 证据：`docs/product/mobile_user_flow.md` 要求普通用户不接触命令行、ROS2、串口和硬件调试，异常需要普通用户可理解。
- 证据：02-03 final 说明 operator HTTP 入口只是 phone-safe support touchpoint，不是正式美观手机端。
- 可执行抓手：本轮只把 remote readiness/status 设计成 phone-readable JSON 字段和文档口径，例如 remote state、last ack、stale status、retry hint、auth/config missing；不做大 UI。

### 推荐 3：O1/HIL 本轮不做主线

- 证据：当前开发机只有 Docker，没有真实 `/dev/ttyUSB0`。
- 证据：历史 HIL sprint 多次因 missing serial device 阻断，证据只能记录为 blocked 或 `software_proof`。
- 可执行抓手：如果执行中需要提及硬件，只写剩余风险；不运行真实 WAVE ROVER 命令，不升级 O1 完成度。

## 3. KR 拆解

| KR | 用户结果 | Owner | 验收口径 |
| --- | --- | --- | --- |
| KR6-1：mock cloud command queue 持久化 | 服务重启后仍能读取未处理命令和已 ACK 状态 | `full-stack-software-engineer` | targeted unittest 覆盖 queue reload、duplicate id、unknown cursor、ack replay |
| KR6-2：robot cursor/status recovery | `remote_bridge` 重启后知道从哪里继续轮询，不重复误执行 terminal ack 命令 | `robot-software-engineer` | targeted remote bridge tests + integration smoke 覆盖 last ack/cursor 文件或状态恢复 |
| KR6-3：bearer/auth readiness | 手机/robot 能区分缺 token、token 不匹配、未配置 cloud endpoint | `full-stack-software-engineer` + `robot-software-engineer` | phone-readable readiness/status 字段稳定，错误不暴露密钥 |
| KR6-4：弱网/重启前的 Docker-only degradation | cloud/status stale 与 retry hint 明确，任务 ACK 和 status 不互相冒充 | `full-stack-software-engineer` | status contract 文档和 targeted tests 覆盖 stale/unknown/not processed |
| KR5-1：phone-readable remote status | 普通手机用户看到的是可理解状态，不是 raw JSON/ROS topic/串口参数 | `full-stack-software-engineer` | `docs/product/remote_4g_mvp.md` 与 `mobile_user_flow.md` 同步更新 |

## 4. 做什么

- 在 local mock cloud 层设计并实现最小持久化命令队列和 ack/status 恢复。
- 在 `remote_bridge` 层明确 cursor 状态边界，优先支持跨进程/跨重启 continuation。
- 增加 phone-readable remote readiness/status 字段，给未来手机端直接消费。
- 更新相关 product docs，明确 Docker-only proof 与真实云/4G/HIL 的边界。
- 用现有 targeted tests、`py_compile` 和 scoped `git diff --check` 验证。

## 5. 不做什么

- 不做正式手机 UI 视觉系统、登录账号、原生 app 或大屏页面。
- 不做生产云部署、HTTPS/TLS、域名、防火墙或 SIM 实测。
- 不实现 OSS/CDN 图片上传链路。
- 不修改硬件配置、vendor 文件、串口参数或 WAVE ROVER 协议。
- 不把 local mock cloud 的 ACK 当作真实送达、Nav2/fixed-route、WAVE ROVER 或 HIL 证据。

## 6. 优先级和验收口径

P0：

- command queue/ack/status 具备可恢复语义。
- `remote_bridge` cursor 边界可跨重启复盘。
- phone-readable readiness/status 不暴露 raw ROS/hardware detail。
- targeted tests、`py_compile`、scoped diff check 通过。

P1：

- status stale/retry hint 和 auth readiness 字段更细。
- 文档补齐未来真实云部署前的 contract checklist。

P2：

- 真实云、HTTPS/TLS、SIM/4G、OSS/CDN、正式手机 UI；这些进入后续 sprint。

## 7. 风险、阻塞和证据链

- 风险：队列持久化实现如果只覆盖 happy path，会在重启后重复执行 command；验收必须覆盖 duplicate id、terminal ack、unknown cursor。
- 风险：phone status 如果把 ACK 写成 completed，会误导用户以为送达完成；验收必须区分 command accepted、robot status、delivery result。
- 风险：bearer token 不能写入 tracked 文件或日志；验收必须确认文档只写环境变量/占位符。
- 阻塞：本机无真实硬件和真实 4G/SIM，本轮只能形成 Docker-only software proof。
- 证据链：执行阶段必须在 `tech-done.md` 记录每条 owner 线的命令输出和失败定位；验收阶段再写 `side2side_check.md` 与 `final.md`。
