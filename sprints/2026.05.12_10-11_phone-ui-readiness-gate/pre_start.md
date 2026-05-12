# Sprint 2026.05.12_10-11 Phone UI Readiness Gate - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 10:11 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 建议主责 Engineer：`full-stack-software-engineer`
- 证据边界：`software_proof_docker_local_phone_ui_readiness_gate`
- 当前约束：本机没有真实硬件，只有 Docker/local；本轮不得声明 HIL、真实 4G、真实云、真实送达或 WAVE ROVER 证据。

## 用户价值和产品北极星

北极星保持不变：普通用户只用手机完成 trash delivery 的发车、状态查看、异常理解和人工恢复，不需要 SSH、ROS2、串口或硬件知识。

本轮用户价值是把 O5 从“operator/debug 页面 + phone-safe fields”推进到一个 Docker/local 可验收的正式手机入口 readiness gate。交付结果应让普通用户在一个手机优先入口里看懂：

- 远程控制是否可用，以及不可用时下一步该做什么。
- backup/restore/preflight 是否只是上线前检查或恢复演练，不等于真实云或真实送达。
- 当前 delivery command 是否 pending、acked、failed、ignored 或需要等待 robot status。
- 失败时是否能人工恢复，而不是看到 raw JSON、ROS topic、串口、WAVE ROVER 参数或 `/cmd_vel`。

## 证据来源

- `OKR.md`：2026-05-12 09:10 快照显示 O5 约 33%，O6 约 34%，O1/O2/O3/O4 约 74-76%；按“优先推进 OKR 完成度低的部分”，本轮优先 O5。
- `sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/final.md`：上一轮 O6 backup/restore drill 已 landed，但 O5 不提升，因为仍“未交付正式手机 UI”。
- `sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/tech-done.md`：已有 Docker/local backup/restore drill、preflight artifact check、robot compatibility 证据，但边界是 `software_proof_docker_backup_restore_drill`。
- `docs/product/mobile_user_flow.md`：手机端最小流程、`phone_copy`、`speaker_prompt`、`remote_readiness` 和 elevator assist phone copy 是用户入口的产品契约。
- `docs/product/remote_4g_mvp.md`：正式 4G 路径是 phone -> cloud API -> robot outbound polling；local/operator 只是 fallback，remote readiness/preflight/backup restore 都必须保持 software-proof 边界。
- `docs/interfaces/ros_contracts.md`：`operator_gateway` 的 `/api/status`、`/api/diagnostics`、`phone_copy`、`remote_readiness.safe_phone_copy`、hardware proof、route proof 等字段是手机 UI 可以消费的接口边界。

## 上轮未完成项和阻塞

- O5 仍缺正式手机 UI、美观/可用验收和普通用户路径；已有 phone-safe/readiness/backend proof 只能支撑 UI，不等于 UI 完成。
- 多轮 O6 已产生 remote readiness、auth degradation、Docker relay、preflight、SQLite state、backup/restore drill；继续只做 O6 backend 会继续让 O5 停留在约 33%。
- 本机 Docker/local 可继续做软件证明，但不能补真实手机 app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 旧 `test_*review*py` -> `NO TESTS RAN` 是验收命令风险；本轮必须使用真实存在的 full-stack unittest 文件名。

## 本轮核心抓手

P0：由 `full-stack-software-engineer` 单 owner 做 phone UI readiness gate，具体实现文件由工程 owner 在 tech-plan 范围内决定。产品要求是：把 operator 手机入口或 phone-safe readiness snapshot/API 聚合成一个普通用户能读懂的手机入口，不再只是 debug 字段堆叠。

P0 聚合内容必须覆盖：

- remote readiness：`remote_ready`、`degradation_state`、`retry_hint`、`safe_phone_copy`、auth/status/command pending 状态。
- backup/restore/preflight：明确 local drill / preflight blocked / artifact valid 等状态是上线前检查或恢复演练，不代表真实云或真实送达。
- delivery command state：collect / confirm_dropoff / cancel 的 pending、ACK、失败和等待 robot status 的用户解释。
- 人工可恢复提示：status stale、auth failed、cloud unreachable、malformed response、preflight blocked、backup restore blocked 时给普通用户下一步。

P1：在不扩大实现面的前提下，改善手机首屏可读性、主路径聚合、触控尺寸、状态层级和中文优先文案；不能为了美观引入无后端契约的 mock 状态。

## 做什么 / 不做什么

做：

- 创建一个 Docker/local 可验收的 phone UI readiness gate。
- 使用现有 `operator_gateway` / remote relay / diagnostics 契约中的 phone-safe 字段。
- 保持普通用户文案与技术诊断分层：用户看恢复建议，工程支持仍可查 diagnostics。
- 只用 fenced validation，不做 broad smoke。

不做：

- 不做真实手机原生 app。
- 不做真实云、真实 4G/SIM、HTTPS/TLS 公网入口或生产账号。
- 不做 OSS/CDN 实流量、STS、CDN 回源或生产 rotate。
- 不做 HIL、真实送达、Nav2/fixed-route、WAVE ROVER 或串口验证。
- 不改硬件协议、vendor 资料、launch 硬件参数或机器人运动链路。
- 不把 ACK 解释成 delivery success。

## 优先级和验收口径

- P0：手机入口能一屏聚合 remote readiness、backup/restore/preflight、delivery command state 和可恢复提示。
- P0：输出不泄露 bearer token、Authorization header、raw cloud URL secret、raw JSON traceback、ROS topic、串口、baudrate、WAVE ROVER 参数、`/cmd_vel` 或硬件配置。
- P0：所有状态保持证据边界：Docker/local software proof 不能写成真实云、真实 4G、真实送达或 HIL。
- P0：targeted full-stack unittest、py_compile、必要 local/script smoke 和 scoped `git diff --check` 通过。
- P1：手机端视觉和交互满足基本 phone-first 可用性，主路径不超过三步，用户不需要理解 ROS2 或云实现细节。

## 责任 Engineer

- 主责：`full-stack-software-engineer`
- 支撑咨询：如实现中发现 ROS2/status 契约字段不足，由 `robot-software-engineer` 只读补接口事实；本轮默认不并行改 robot/autonomy/hardware。
- Product Owner 收口：后续验收时更新 `tech-done.md`、`side2side_check.md`、`final.md`，并按证据决定是否保守上调 O5。

## 需要创建或更新的 sprint 文档

本轮规划阶段只创建：

- `sprints/2026.05.12_10-11_phone-ui-readiness-gate/pre_start.md`
- `sprints/2026.05.12_10-11_phone-ui-readiness-gate/prd.md`
- `sprints/2026.05.12_10-11_phone-ui-readiness-gate/tech-plan.md`

实现完成后必须更新：

- `tech-done.md`：实际改动、验证结果、偏差、证据边界。
- `side2side_check.md`：对照 PRD 验收、不得宣称事项。
- `final.md`：OKR 变化、剩余风险、下一步。
