# Sprint 2026.05.12_02-03 Remote 4G Command Loop - PRD

## 状态

- 阶段：prd
- 时间：2026-05-12 02:03 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主目标：O6 4G 云中转从文档 contract 推进到 Docker-only 本地可验证闭环
- 验收边界：`software_proof_docker_only`

## 用户价值

普通用户最终只应通过手机发起垃圾投递任务、查看当前状态和处理异常，而不需要知道小车 IP、WiFi、SSH、ROS2 topic、串口或底盘协议。本轮先做最小云中转闭环，让“手机/脚本 -> cloud API -> robot outbound polling -> behavior-level command -> ack/status -> 手机/脚本”在本机 Docker 环境内跑通。

这一步解决的是 O6 的最低完成度缺口：现有 `docs/product/remote_4g_mvp.md` 已定义合同，但没有可运行云服务、robot polling 或可读 ack/status 链路。没有这个闭环，O5 手机端只能停留在本地 operator fallback，不能支撑正式 4G 产品路径。

## 产品北极星

本轮对北极星的贡献是把“普通手机用户远程下发任务”从愿景变成最小可验证控制面。目标不是直接完成真实 4G，也不是替代 HIL；目标是建立云端中转控制面的第一条可测试产品路径。

## OKR 映射

| OKR | 当前证据 | 本轮目标 | 不计入本轮 |
| --- | --- | --- | --- |
| O6 4G 云中转 + OSS/CDN | 约 5%；已有 cloud API contract 和基础设施方向，云端服务未实现 | 建立本地 mock cloud / cloud API / remote bridge command-status-ack 闭环 | 真实云部署、OSS/CDN、STS、生产鉴权、SIM、弱网 |
| O5 手机体验与量产边界 | 约 30%；美观可用手机入口仍缺 | 只做最小 phone-safe command/status/ack 入口，服务 O6 闭环 | 大 UI 重构、视觉设计系统、账号体系 |
| O2 可恢复任务闭环 | 约 74%；任务证据链已有软件基础 | remote command 只进入 behavior-level 合同，不绕过状态机 | 真实 delivery/nav 完成率提升 |
| O1/O3 | 约 75%；真实硬件 blocked | 保持证据边界，不抢主线 | HIL、真实串口、真实 route replay |

## KR 拆解

### KR-A：Cloud command queue

用户或脚本可以向本地 mock cloud 提交 command，cloud 按 `robot_id` 保存待处理命令，并支持 robot 按 `last_ack_id` 拉取下一条。

验收：

- `collect` command 带非空 `target` 可进入队列。
- `confirm_dropoff` 和 `cancel` 可进入队列。
- 缺 `id`、未知 `type`、非对象 `payload`、过期 command 不会进入可执行队列或会被 bridge ack 为 `failed` / `ignored`。
- duplicate `id` 不造成重复执行。

### KR-B：Status and ack loop

robot bridge 可以 post status 和 command ack，phone/web/script 可以读取最新状态和 ack。

验收：

- `POST /robots/{robot_id}/status` 保存 `protocol_version`、`robot_id`、`state`、`message`、`updated_at`。
- `POST /robots/{robot_id}/commands/{command_id}/ack` 保存 `acked` / `failed` / `ignored`。
- command ack 不被误写成 delivery final result；后续 delivery 状态必须由 status 表达。

### KR-C：Remote bridge outbound polling

robot 侧只发起 outbound HTTP 请求，不要求 cloud inbound 连接小车，不暴露 ROS2 原始控制接口。

验收：

- bridge 轮询 `GET /robots/{robot_id}/commands/next?last_ack_id=<id>`。
- bridge 对 `collect` 调用 behavior-level contract 或本地 mock adapter。
- bridge 对 `confirm_dropoff` / `cancel` 调用对应 behavior-level contract 或 mock adapter。
- bridge 针对 expired / malformed / duplicate / busy 返回确定 ack。
- bridge 不接受、透传或暴露 `/cmd_vel`。

### KR-D：Phone-safe minimum entry

O5 只作为 O6 的用户入口支撑。

验收：

- 有一个页面、local web route 或脚本入口可以提交 command。
- 有一个状态/ack 查看入口可以给普通用户看到任务是否已提交、被忽略、失败或需要人工处理。
- 页面或输出不要求用户理解 ROS2、串口、Docker、HIL 或 `/cmd_vel`。

## 做什么

- 实现本地 mock cloud API，遵循 `docs/product/remote_4g_mvp.md` 的 command/status/ack contract。
- 实现或接入 robot `remote_bridge` outbound polling。
- 实现最小 phone-safe command/status/ack 入口。
- 使用 Docker/local mock 行为适配层验证闭环，不要求真实硬件。
- 完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`，并在最终收口中明确证据边界。

## 不做什么

- 不做生产云部署、域名切流、TLS、账号/权限、token rotation、STS、OSS/CDN 图片链路。
- 不做真实 SIM、真实 4G 网络、弱网和断网恢复。
- 不做大 UI 重构，不把 O5 完成度当主目标。
- 不改 WAVE ROVER、ESP32、UART、引脚、电压、机械、vendor 文档或硬件配置。
- 不把 ack 解释成真实垃圾送达完成。
- 不提升 O1/HIL 或 O3 实机完成度。

## 责任 Engineer

| Owner | 责任 |
| --- | --- |
| `full-stack-software-engineer` | mock cloud API、最小 phone-safe command/status/ack 入口、API contract 测试 |
| `robot-software-engineer` | remote bridge outbound polling、behavior-level mock adapter、bridge command validation 与 ack/status loop |
| `product-okr-owner` | 验收口径、OKR 边界、sprint 留档收口 |
| `hardware-engineer` | 本轮不实现；仅当有人试图引入真实硬件细节时做 vendor 事实核对 |
| `autonomy-engineer` | 本轮不实现；不新增 route/Nav2 主线任务 |

## 优先级

- P0：command -> polling -> ack/status 最小闭环。
- P0：contract validation 和安全边界，不暴露 `/cmd_vel`。
- P1：phone-safe 最小入口。
- P1：Docker-only 验证和 scoped tests。
- P2：真实云、OSS/CDN、生产鉴权、弱网、真实 4G，全部延期。

## 验收口径

本轮实施完成时，必须能给出以下证据：

- 本地 mock cloud API 可启动或可被测试实例化。
- 至少一个命令从提交到 bridge 轮询到 ack/status 回写的端到端测试通过。
- malformed、expired、duplicate、busy 至少覆盖为围栏测试或脚本断言。
- 最小 phone-safe 入口能提交 command 并读取 status/ack。
- 验证命令为 targeted tests、`py_compile`、Docker/local smoke、scoped `git diff --check`，不做 broad regression。
- 所有结论标注为 `software_proof_docker_only`，不声明真实 4G、真实云、真实硬件或 HIL。

## 风险和阻塞

- 当前主机没有真实硬件，不能产生 HIL、真实底盘运动或真实 route replay 证据。
- 当前没有真实 4G SIM 或云部署，不能证明公网可达、运营商 NAT、弱网恢复或生产 token 安全。
- 如果实现时发现现有 phone/web 入口结构不适合快速接入，应优先交付脚本级 phone-safe 入口，不启动大 UI 重构。
- 如果 ROS2 runtime 在 Docker 内启动成本过高，允许 bridge 使用 behavior-level mock adapter 证明 contract loop，但必须在 `tech-done.md` 明确剩余集成风险。

## 需要更新的 sprint 文档

- 当前阶段：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现后：`tech-done.md` 必须记录实际改动、验证命令和输出。
- 验收后：`side2side_check.md` 必须记录与 PRD 的对照。
- 收口后：`final.md` 必须记录 OKR 影响、证据边界和下一轮风险。
