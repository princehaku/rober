# O6 Artifact Bundle Ingest Pre Start

## Sprint 类型

- sprint_type: epic
- start_time: 2026-07-09 08:56 CST
- product_owner: product-okr-owner
- implementation_owner: robot-software-engineer
- target_objective: O6
- secondary_objective: O7 consumer readiness only
- evidence_boundary: software_proof_local_mock_artifact_bundle_ingest_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 上轮状态和阻塞核对

最近两轮 O6/O7 epic 均以软件证据通过收口，不是 blocked 收口：

- `sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/` 完成 local/mock annotation submit/export。
- `sprints/2026.07.09_07-55_o6_artifact_seed_media_preflight/` 完成 `artifact_media_preflight` 和 O7 消费展示。

两轮共同留下的下一步是“真实或现场 artifact seed 进入 O6 archive，并由 consumer read/O7 主路径消费”。当前环境没有真实生产云、OSS/CDN、4G/TLS 或真实媒体读取凭证，因此本轮选择不依赖外部条件的最低 O6 增量：接收结构化 artifact bundle 摘要，转成可回读的 archive task、trajectory、events、evidence refs 和 media preflight 输入。

## 本轮目标

把 O6 从“可以接收 field evidence manifest 和 media preflight 摘要”推进到“可以接收 route/replay/keyframe/evidence 的结构化 artifact bundle 摘要，并在同一 `task_id` 下形成可查询的 O6 archive/consumer read 模型”。

本轮不读取真实文件、不访问 OSS/CDN、不连接 production DB/queue、不启动 ROS2 runtime、不下发机器人控制。所有能力都保持 local/mock、not_proven 和 fail-closed。

## Owner 和协作边界

- Robot Software Engineer：实现 O6 artifact bundle ingest、测试、接口文档和 `tech-done.md`。
- Product / Main：只做拆解、派单、验收和最终 sprint 收口。
- Full-Stack：本轮不改 O7 代码；O7 只作为后续 consumer 受益方。

## 验收口径

- 新增或扩展 O6 local/mock ingest API，可接收结构化 bundle 摘要并写入同一 file-backed store。
- 写入后 `GET /api/o6/archive/tasks/<task_id>` 和 `GET /api/o6/consumer/tasks/<task_id>?include=trajectory,events,evidence,field_evidence` 能读到派生的 trajectory/events/evidence refs/media preflight 或等价安全摘要。
- 危险字段、credential/raw path/base64/raw media/控制能力声明必须 fail-closed，不写 store。
- 文档同步更新 `docs/interfaces/o6_cloud_archive_api.md`。
- `tech-done.md` 记录实际改动、验证输出和剩余风险。
