# Sprint 2026.05.12_06-07 Remote Cloud Entry Docker Deploy - Side By Side Check

## 状态

- 阶段：side2side_check
- 更新时间：2026-05-12 07:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 验收结论：有条件通过
- 证据边界：`software_proof_docker_deploy`

## 用户价值和产品北极星

本轮把 O6 remote cloud relay 从本机 Python proof 推进到 Docker deploy proof。用户价值不是“用户已经能用正式手机 App 控车”，而是未来手机入口和 robot outbound polling 有了更接近云入口形态的服务：容器可启动、配置走 env、可检查 health/readiness、credential gate 可验证、command/status/ack 契约可在容器入口跑通。

北极星保持不变：普通用户只用手机，不接触 ROS2、SSH、串口、`/cmd_vel` 或硬件参数，通过 4G 云中转完成 trash delivery。本轮只是云控制面入口的部署 proof，不是实机送达闭环。

## OKR 映射

| Objective/KR | 验收判断 |
| --- | --- |
| O6 KR1 云中转最小契约 | 通过。`trashbot.remote.v1` commands/status/ack 在 Docker relay smoke 中完成 status、command、next、ack、readback。 |
| O6 KR2 云服务端基线 | 部分通过。Dockerfile、compose、env 和 health/readiness 已形成 production-shaped proof；真实公网云、HTTPS/TLS、防火墙和生产持久化仍未完成。 |
| O6 KR5 凭证管理 | 通过本轮围栏。`.env.example` 只放占位，readiness/error/state 边界要求不回显 bearer token、Authorization、credential URL、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。 |
| O6 KR6 graceful degradation | 部分通过。readiness 和 phone-safe failures 支撑未来手机/运维区分服务未就绪、鉴权失败、状态缺失和存储问题；真实 4G 弱网恢复未验证。 |
| O5 KR5/KR7 支撑 | 只算 readiness/status 支撑，不算正式手机 UI 或普通用户验收完成。 |
| O1/O2/O3/O4 | 不提升。本轮没有硬件、Nav2/fixed-route、相机或 HIL 证据。 |

## KR 拆解或更新

- O6 可保守小幅上调：Docker deploy proof 比上一轮 independent local relay 更接近可部署云入口，新增了 health/readiness、compose env、container smoke 和 robot compatibility fence。
- O5 不建议上调：本轮只提供 phone-safe readiness/status API 支撑，尚无美观正式手机 UI、主流手机尺寸验收、普通用户实机流程或 4G 手机端端到端 proof。
- O1/O2/O3/O4 不更新：本轮证据不能证明 WAVE ROVER、Nav2/fixed-route、相机感知或 HIL。

## Side By Side 对照

| PRD/Tech Plan 验收项 | 工程证据 | Product Acceptance |
| --- | --- | --- |
| Docker startup | `scripts/remote_cloud_relay_docker_smoke.sh` 输出 `ros-rbs-remote-cloud-relay:dev Built`，container started，cleanup passed。 | 通过。证明本机 Docker deploy proof 可重复启动。 |
| Health/readiness | `/healthz` 返回 service/protocol/evidence boundary；`/readyz` 返回 credential gate、state store、phone-safe failure checks true。 | 通过。可作为未来 phone diagnostics/运维入口的 readiness 基线。 |
| Command/status/ack smoke | Docker smoke 覆盖 post status、enqueue command、robot-style next、post ack、read ack/status。 | 通过。ACK 仍只代表 command envelope 处理，不代表真实送达。 |
| Robot client compatibility | `test_remote_bridge_protocol.py` + `test_remote_bridge.py`：`Ran 31 tests in 15.223s OK`；remote bridge py_compile exit 0；Docker smoke exit 0。 | 通过。兼容性围栏充分，未扩大到宽泛回归。 |
| Targeted relay tests | `test_remote_cloud_relay.py`：`Ran 8 tests in 4.167s OK`；`remote_cloud_relay.py` py_compile exit 0；scoped diff check exit 0。 | 通过。覆盖 relay 新增 endpoint 和 readiness 语义。 |
| Docs sync | `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md` diff 已同步 Docker deploy proof、health/readiness 与证据边界。 | 通过。文档没有把 proof 写成真实云。 |
| 安全边界 | `.env.example` 仅占位；readiness/error 脱敏 contract 写入 docs 和 tech-done。 | 通过本轮软件围栏；真实生产 secret provisioning/rotate 未完成。 |

## 做什么 / 不做什么

本轮已做：

- Docker/compose/env 入口。
- `/healthz` 与 `/readyz`。
- command/status/ack Docker smoke。
- robot client compatibility fence。
- 产品文档同步。

本轮未做且不得冒充完成：

- 真实云主机、公网入口、HTTPS/TLS、防火墙实配。
- 真实 4G/SIM、弱网或 carrier 测试。
- OSS/CDN、STS、受限 AK、生命周期和 rotate。
- 正式手机 UI、美观验收或普通用户实机验收。
- Nav2/fixed-route、WAVE ROVER、真实送达或 HIL。

## 风险、阻塞和证据链缺口

- `software_proof_docker_deploy` 只证明控制面入口形态和容器烟测，不证明生产云可靠性。
- `FileBackedRelayStore` 仍是单机 proof store，生产需要 DB/queue、备份、审计、多实例一致性和 provisioning。
- readiness 首次等待出现过 `curl: (56) Recv failure: Connection reset by peer` 后重试成功，属于容器启动窗口期，已记录为非阻断。
- Python 3.13 robot unittest 出现 `ResourceWarning` 后仍 `OK`，当前不阻断 contract 结论，但后续可在测试服务 teardown 中收敛。

## Product Acceptance

Product 接受本轮作为 O6 的 `software_proof_docker_deploy` 收口。OKR 只允许 O6 小幅上调；O5 仅记录 phone-safe readiness 支撑，不提升正式手机体验进度；O1/O2/O3/O4 不提升。
