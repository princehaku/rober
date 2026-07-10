# O6 Artifact Bundle Ingest PRD

## 用户价值和产品北极星

O6 的下一步价值不是继续展示缺口，而是让现场或离线产生的路线材料能进入统一 archive/read 模型。普通用户最终需要的是“垃圾投递任务可复盘、可诊断、可训练”，开发者和运营需要先把 route/replay/keyframe/evidence 这类材料归档成同一个 `task_id` 的可查询数据。

本轮只做 software proof：通过结构化 local/mock artifact bundle 摘要推进 O6 KR2/KR3/KR6，不声明真实云、真实媒体、真实机器人运动或 delivery success。

## 需求范围

必须实现：

- O6 接收一份小型结构化 artifact bundle 摘要，字段表达 route/replay/keyframe/evidence refs、trajectory frames 和 events。
- 入口必须复用或兼容现有 local/mock archive store，不引入生产 DB 或外部依赖。
- bundle 写入后，archive task detail 和 consumer read detail 能在同一 `task_id` 回读轨迹、事件、证据引用和 artifact/media 预检摘要。
- 危险字段和真实能力声明 fail-closed：`safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`robot_control_executed=true`、`connects_cloud_production=true`、`real_cloud_db_connected=true`、`real_oss_connected=true` 均不得通过。
- 禁止回显绝对路径、credential URL、token/password/secret、base64/raw media、串口路径、`/cmd_vel` 或 traceback。

非目标：

- 不读取真实 `route.csv`、JSONL、rosbag 或 keyframe 文件内容。
- 不做 OSS/CDN fetch smoke。
- 不改 O7 UI。
- 不连接生产云、真实隧道、4G/TLS 或机器人控制链路。

## OKR 映射

- O6 KR2：任务记录、轨迹帧、事件和失败/状态摘要进入 archive/read model。
- O6 KR3：大对象仍只保存 `evidence_ref` / media ref 摘要，不存原始大文件。
- O6 KR6：consumer read API 能消费同一 `task_id` 的 artifact bundle 派生数据。

## 验收信号

- 单元测试覆盖 happy path、consumer read 回读、危险字段拒绝、unsafe ref 拒绝、缺关键数据拒绝。
- 文档明确该能力是 `software_proof_local_mock_artifact_bundle_ingest_only`。
- `tech-done.md` 引用实际验证命令和输出。
