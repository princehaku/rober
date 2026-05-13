# Sprint 2026.05.13_08-09 Cloud Public Ingress TLS Gate - Side2Side Check

## 验收对象

- Task A：`software_proof_docker_cloud_public_ingress_tls_gate` 云中转公网入口/TLS 配置 gate。
- Task B：robot-side metadata-only compatibility fence。
- Task C：产品收口、OKR 当前快照和 OKR 进度日志同步。

## 用户价值对照

| 项目 | 预期 | 实际 |
| --- | --- | --- |
| 手机/云端 readiness 可解释性 | 区分缺配置与配置存在但缺外部实证 | 已区分 `missing_public_ingress_tls_config` 与 `public_ingress_tls_config_present_not_externally_proven` |
| 生产边界 | 不让 Docker/local proof 冒充 production ready | 两条路径均保持 `production_ready=false`、`overall_status=blocked` |
| Robot side effect | readiness metadata 不应触发机器人动作 | Task B targeted tests 证明不触发 backend action、不 POST ACK、不推进或持久化 cursor |
| ACK 语义 | ACK 只能代表 accepted/processing | 文档和 compatibility fence 均保持 ACK 不等于 delivery success |

## OKR 对照

- Objective 5 从约 59% 保守上调到约 61%。
- 进度提升来自公网入口/TLS/反向代理配置 gate、preflight consumption、Docker smoke 覆盖和 robot side-effect fence。
- Objective 1/2/3/4 不调整，因为本轮未新增硬件、任务闭环、导航或手机真实设备证据。

## 不声明事项

本轮不声明真实 HTTPS/TLS、公网入口、真实云、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、production disaster recovery、真实手机设备/browser、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 验证证据

- Task A targeted relay unittest：首轮失败于 evidence boundary 优先级，修复后 `Ran 58 tests in 7.079s OK`。
- Task A `py_compile`：通过，无输出。
- Task A Docker smoke：通过，覆盖 missing/config-present 两条 ingress/TLS gate、preflight、external probe、backup/restore、command/status/ack、SQLite restart。
- Task A scoped diff check：通过，无输出。
- Task B remote bridge/protocol targeted tests：`Ran 72 tests in 35.978s OK`。
- Task B `py_compile`：通过，无输出。
- Task B scoped diff check：通过，无输出。
- Task B 运行中存在一个本任务范围外既有 `ResourceWarning`，exit 0。

## 剩余证据缺口

下一步要关闭的不是更多本地 metadata，而是真实外部 HTTPS/TLS、DNS、公网反向代理、防火墙路径、真实云部署、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性和灾备演练证据。所有这些缺口关闭前，Objective 5 仍只能按 software proof 保守推进。
