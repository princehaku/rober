# O6 Artifact Bundle Ingest Side-by-Side Check

## Sprint 类型和证据边界

- sprint_type: epic
- product_owner: product-okr-owner
- evidence_boundary: software_proof_local_mock_artifact_bundle_ingest_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## PRD 验收逐项对照

| PRD 验收口径 | 证据 | 结论 |
| --- | --- | --- |
| O6 接收结构化 artifact bundle 摘要，字段表达 route/replay/keyframe/evidence refs、trajectory frames 和 events | Robot worker 摘要与 `tech-done.md` 明确新增 `POST /api/o6/archive/artifact-bundle`，接受 `trashbot.o6.artifact_bundle.v1`，并把 route/replay/keyframe/evidence refs、trajectory frames、events 转成 archive 数据。 | 通过 |
| 入口复用现有 local/mock archive store，不引入生产 DB 或外部依赖 | 实现摘要说明复用 file-backed O6 archive store，把 bundle 写入同一 `task_id` 的 task、trajectory、events、evidence refs 和 `artifact_media_preflight`。 | 通过，边界为 local/mock |
| 写入后 archive task detail 和 consumer read detail 可在同一 `task_id` 回读轨迹、事件、证据引用和 artifact/media 预检摘要 | `tech-done.md` 与 worker 摘要说明 archive task detail / consumer detail 新增 `artifact_bundle`、`artifact_bundle_consumer_ingest` additive alias，并继续回读 `artifact_media_preflight`。 | 通过 |
| `field-evidence` 兼容 wrapper 或直传 bundle，不破坏既有合同 | 实现摘要说明 `POST /api/o6/archive/field-evidence` 在收到 `artifact_bundle` wrapper 或直传 `trashbot.o6.artifact_bundle.v1` 时走同一 ingest 逻辑。 | 通过 |
| 危险字段、真实能力声明、绝对路径、credential URL、token path、base64/raw media、unsafe refs 必须 fail-closed | 新增测试覆盖 empty refs / dangerous true / unsafe ref fail-closed；`tech-done.md` 明确 `dangerous true`、empty refs、unsafe refs 继续拒绝写 store。 | 通过 |
| 单元测试覆盖 happy path、archive detail / consumer detail 回读、兼容 alias 和 fail-closed 路径 | `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 151 tests in 50.374s`、`OK`；本轮新增 artifact bundle happy path、archive detail / consumer detail 回读、`field-evidence` alias 和 fail-closed 测试。 | 通过 |
| 接口文档同步更新，写清 local/mock 证据边界 | worker 摘要说明已更新 `docs/interfaces/o6_cloud_archive_api.md`，补充 `POST /api/o6/archive/artifact-bundle` 合同、`field-evidence` alias 与 readback alias。 | 通过 |
| `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险 | 本目录 `tech-done.md` 已写明 151 tests、`py_compile`、`git diff --check` 和风险边界。 | 通过 |

## 危险字段核对

本轮所有真实能力字段继续保持 fail-closed：

- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false
- connects_cloud_production: false
- real_cloud_db_connected: false
- real_oss_connected: false
- cloud_write_executed: false
- real_media_read_executed: false

## 用户价值和产品北极星对照

- 用户价值：现场或离线产生的 route/replay/keyframe/evidence 摘要现在可以围绕同一 `task_id` 进入 O6 archive/read 主链路，运营和开发者能更接近“可复盘、可诊断、可训练”的统一数据模型。
- 产品北极星：仍服务于“可验证地可靠送垃圾”的长期目标；本轮只推进 O6 数据底座，不证明真实送达、真实云链路、真实媒体可读或控制能力。

## OKR 映射和方向判断

- O6 KR2：任务记录、轨迹帧、事件和失败/状态摘要进入 archive/read model 的合同更完整。
- O6 KR3：大对象仍只保存 `evidence_ref` / media ref 安全摘要，没有落原始大文件。
- O6 KR6：consumer read API 现在可围绕同一 `task_id` 消费 `artifact_bundle` 派生数据。
- 方向判断：继续 O6，但下一步必须消费真实 `route.csv`、replay JSONL、keyframe 或 rosbag，而不是继续堆只读摘要层。

## 收口判断

本 sprint PRD 验收口径成立，closeout 轻量命令应确认 `tech-done.md`、`side2side_check.md`、`final.md` 存在，关键字段可检索，且 `git diff --check` 通过。验收边界必须写为 `software_proof_local_mock_artifact_bundle_ingest_only`。

本轮不证明真实 `route.csv`、replay JSONL、keyframe 或 evidence 文件存在或可读，不证明真实云、OSS/CDN、4G/TLS、真实机器人、O7 真实回放或 delivery success。
