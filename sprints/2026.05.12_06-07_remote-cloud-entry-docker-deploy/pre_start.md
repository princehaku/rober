# Sprint 2026.05.12_06-07 Remote Cloud Entry Docker Deploy - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据目标：`software_proof_docker_deploy`
- 环境边界：本机只有 Docker，没有真实硬件、真实 4G/SIM、真实云主机或 HIL。

## 用户价值和产品北极星

本轮用户价值是把上一轮 independent local relay service 从“能在本机 Python 运行”推进到“具备生产形态的 Docker 部署入口”。普通用户未来只用手机访问云端 API，小车通过 4G outbound polling 云端控制面；当前 sprint 不做正式手机 UI，而是先把云入口服务的容器运行、环境变量、health/readiness 和机器人客户端兼容性证明出来。

产品北极星保持不变：普通用户不接触 ROS2、SSH、串口、`/cmd_vel` 或硬件参数，也能通过手机入口发起和理解 trash delivery。当前阶段的抓手是 O6 云中转可部署入口，不是 HIL、真实 4G、OSS/CDN 或正式 UI。

## 当前仓库证据

- `OKR.md` 当前快照显示 O6 约 23%，O5 约 33%；O1/O2/O3 仍受真实硬件、Nav2、fixed-route 和 HIL 证据限制。
- `sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/final.md` 的 Next Recommendations 明确建议先做 O6 最小真实云入口 proof，并说明 05-06 只完成 independent Docker/local relay service，不等于真实云、HTTPS、4G、OSS/CDN。
- `sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md` 已证明 `remote_cloud_relay.py`、file-backed persistence、bearer auth、phone-safe errors 和 robot client compatibility，但证据边界仍是 `software_proof_docker_only`。
- `docs/product/cloud_4g_infrastructure.md` 明确真实云仍缺公网 HTTPS、TLS、防火墙、生产持久化、OSS/CDN、运维边界；当前 Docker/local proof 默认建议监听 `127.0.0.1`。
- 用户本轮约束是“功能往前走”“别测试代码一堆，测试只围栏”“优先推进 OKR 完成度低的部分”“本机没有真实硬件，只有 Docker”“最后提交 git 并推送远程”。

## OKR 映射

| Objective | 本轮处理 |
| --- | --- |
| O6 4G 云中转 + OSS/CDN | 主线推进。把 independent relay 推到 production-shaped Docker deploy proof，补容器入口、compose/env 占位、health/readiness、host/container smoke 和 robot client compatibility smoke。 |
| O5 手机体验与量产边界 | 只做 phone-safe status/readiness 支撑，帮助后续手机 UI 判断服务可用性；不提升正式手机 UI 完成度。 |
| O1/O2/O3 | 不作为本轮主线。无真实硬件、Nav2、fixed-route 或 HIL，不能声明相关完成度提升。 |
| O4 | 不涉及。 |

## 上轮未完成项和本轮继承

- 真实云部署、HTTPS/TLS、公网入口、防火墙实配仍未完成；本轮只能做到 Docker deploy proof。
- 真实 4G/SIM、弱网/断网 carrier 测试仍未完成；本轮不伪造网络实测。
- OSS/CDN 上传、STS、受限 AK、生命周期和 rotate 仍未完成；本轮仅保留 env 占位和产品边界。
- production DB/queue、多实例一致性、备份、灾备仍未完成；本轮仍可使用 file-backed proof，但要写清生产缺口。
- ACK 仍只代表 command envelope 处理状态，不代表真实导航、投放、返回或任务完成。

## 本轮核心抓手

核心抓手是 O6 `remote_cloud_entry_docker_deploy_proof`：

1. 提供可重复的 Docker 容器入口，让 relay service 可在容器中启动。
2. 提供 compose/env 占位，明确 bearer token、state path、host/port、future HTTPS/OSS/CDN 配置边界。
3. 提供 health/readiness API 或等价检查，让手机/运维能区分服务启动、鉴权配置、state store 可写和 status 可用性。
4. 提供 host/container smoke，证明本机 Docker 环境能启动服务并完成 command/status/ack 最小闭环。
5. 保持 robot client compatibility smoke，证明 `RemoteCloudClient` 仍可对接容器化 relay。

## 做什么 / 不做什么

做：

- 创建生产形态 Docker deploy proof。
- 保持 `trashbot.remote.v1` commands/status/ack 契约。
- 明确环境变量和 `.env.example` 仅放占位，不提交真实密钥。
- 增加 health/readiness 或等价 endpoint/check。
- 增加有限 smoke，覆盖 host/container 与 robot client 兼容。
- 同步相关 `docs/product/` 文档和当前 sprint `tech-done.md`。

不做：

- 不部署真实云主机、域名、公网 HTTPS 或防火墙。
- 不接真实 4G/SIM，不声明弱网或 carrier proof。
- 不实现 OSS/CDN、STS、受限 AK、CDN 回源或生命周期。
- 不做正式手机 UI、美观验收或普通用户实机验收。
- 不跑宽泛测试矩阵，不把测试扩成主工作量。
- 不声明 HIL、WAVE ROVER、Nav2/fixed-route 或真实送达完成。

## 优先级和验收口径

| 优先级 | 验收口径 |
| --- | --- |
| P0 容器入口 | Docker image 或 compose 能启动 independent relay service，服务配置来自环境变量或显式参数。 |
| P0 readiness | health/readiness 能区分进程存活、bearer token 配置、state store 可写和 phone-safe failure。 |
| P0 command/status/ack smoke | 在容器服务上完成 status post/get、command enqueue/next、ack post/get。 |
| P0 robot client compatibility | `RemoteCloudClient.post_status -> get_next_command -> post_ack` 对容器 relay 兼容。 |
| P0 安全边界 | 错误响应、state file、示例 env 不暴露 bearer token、Authorization header、串口、baudrate、WAVE ROVER 参数、ROS topic 或底层速度入口。 |
| P1 文档同步 | `docs/product/cloud_4g_infrastructure.md` 或相关产品文档同步 Docker deploy proof 与仍未完成的真实云边界。 |

## 责任 Engineer

- `full-stack-software-engineer`：主责 Docker deploy proof、compose/env、health/readiness、container smoke、相关产品文档同步和 `tech-done.md`。
- `robot-software-engineer`：支撑 robot client compatibility smoke，确保容器 relay 不破坏 `RemoteCloudClient` 与 `remote_bridge` 兼容语义。
- `product-okr-owner`：负责 OKR 边界、验收口径、side-by-side check、final 与必要的 OKR 保守更新。

## 风险、阻塞和证据链缺口

- 本轮没有真实云和真实 4G，最终证据最多是 `software_proof_docker_deploy`。
- Docker deploy proof 不能自动提升 O1/O2/O3，也不能证明真实送达。
- health/readiness 只能证明服务入口和配置状态，不代表机器人任务成功。
- file-backed persistence 若继续使用，必须写清不等于生产 DB/queue、多实例一致性或灾备。
- 若 Docker Desktop 或端口占用阻塞 container smoke，必须记录失败命令、原因和替代 host smoke，不能冒充通过。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`
- 本轮前置必须创建：`prd.md`、`tech-plan.md`
- 实现后必须更新：`tech-done.md`
- 验收后必须更新：`side2side_check.md`、`final.md`
