# O6 Artifact Bundle Ingest Final

- sprint_type: epic
- close_time: 2026-07-09 09:08 CST
- product_owner: product-okr-owner
- target_objectives: O6
- secondary_objective: O7 consumer readiness only
- evidence_boundary: software_proof_local_mock_artifact_bundle_ingest_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 用户价值和产品北极星

本轮把 O6 从“能接收 field evidence manifest 和 media preflight 摘要”推进到“能接收 route/replay/keyframe/evidence 的结构化 artifact bundle 摘要，并在同一 `task_id` 下形成 archive/read 主路径回读”。这让现场或离线材料更接近统一归档模型，后续 O7 回放、标注和训练数据链路不用再只围绕单个 wrapper 或孤立摘要拼接。

产品北极星不变：让普通用户把垃圾交给小车后，小车可验证地完成投递。本 sprint 只补 O6 数据底座，不声明真实投递、真实机器人控制、真实媒体可读或真实生产云。

## OKR 映射和方向判断

方向判断：继续 O6，保守上调软件侧进度；O7 不上调，不归档 KR。

- O6 从约 37% 保守上调到约 39%。理由：O6 已新增 `POST /api/o6/archive/artifact-bundle`，可把 `trashbot.o6.artifact_bundle.v1` 结构化摘要写入 file-backed archive store，并在 archive task detail / consumer detail 回读 `artifact_bundle` / `artifact_bundle_consumer_ingest` alias；`test_remote_cloud_relay` 提升到 `151 tests OK`。
- O7 维持约 38%。理由：本轮只是增强 O6 对 O7 的后续消费准备度，没有新增 O7 UI、adapter 或真实消费证据。
- O6 KR2/KR3/KR6 都推进了软件侧合同，但仍不标完成。当前仍缺真实隧道、生产 DB/queue、OSS/CDN、TLS/4G、真实机器人数据、真实媒体可访问和生产级查询容量。

## KR 拆解、更新或历史归档

- O6 KR2：任务记录、轨迹帧、事件与失败/状态摘要现在可以通过 `artifact_bundle` 结构化入口写入 archive/read model。
- O6 KR3：继续只保存 `evidence_ref` / media ref 安全摘要，不落原始大文件，和 KR3 目标保持一致但未证明真实 OSS。
- O6 KR6：archive task detail 与 consumer detail 具备同一 `task_id` 下的 `artifact_bundle` additive alias 回读能力。
- 已完成 KR 历史归档：无。本轮不把任何 KR 标为完成或移入历史区。
- 历史记录位置：`docs/process/okr_progress_log.md` 新增 `2026-07-09 08-56｜o6_artifact_bundle_ingest` 条目。

## 本轮核心抓手

核心抓手是把 route/replay/keyframe/evidence 摘要从“多个局部只读合同”推进到一个明确的 `artifact_bundle` ingest 入口，让 O6 archive/read 模型能围绕同一 `task_id` 写入并回读更完整的结构化材料，同时继续保持所有真实能力 fail-closed。

## 需要做什么

下一步必须直接消费真实证据链，而不是继续叠加 local/mock summary：

1. 让真实 `route.csv`、replay JSONL、keyframe 或 rosbag 进入 O6 archive，并验证至少一类真实 artifact 能被安全消费。
2. 补真实 keyframe/media ref 可访问性 smoke，证明 archive 里的 refs 不只是字符串。
3. 在具备生产 backing 后推进真实 annotation API、真实 dataset export、生产级 archive query 和长期数据回灌。

## 优先级和验收口径

- 当前最高优先级仍是现场 O3 验证 lane，其次 O6、O7。
- O6 下一步验收应要求真实 artifact 至少形成一条可复现的 `route.csv`、replay JSONL、keyframe 或 rosbag 消费证据。
- O7 下一步验收应要求基于真实 artifact 的回放或标注消费链路，而不是继续只依赖 local/mock summary。
- 本轮验收通过的唯一边界是 `software_proof_local_mock_artifact_bundle_ingest_only`。

## 对应责任 Engineer

- `robot-software-engineer`：O6 archive/read model、artifact bundle ingest、真实 artifact seed 接入、生产 backing 前置接口。
- `robot-algorithm-engineer`：提供 route.csv、replay JSONL、keyframe、rosbag 或现场路线证据，避免 O6 继续在摘要层自循环。
- `full-stack-software-engineer`：在 O6 真实 artifact 到位后推进 O7 基于真实材料的回放、标注和媒体消费链路。
- `product-okr-owner`：维护 O6 保守进度、验收边界和 KR 历史归档。

## 风险、阻塞和证据链缺口

- 本轮不证明真实 `route.csv`、replay JSONL、keyframe 或 evidence 文件存在、可读、可播放或可下载。
- 不证明真实 production DB/queue、OSS/CDN、TLS/4G、真实隧道、真实 annotation API、真实 dataset export、真实媒体访问或生产级查询容量。
- 不证明真实机器人控制、真实 O7 回放、真实 RTC/视频、真实 ASR/TTS、wheel raw 非零、真实电梯状态链、真实长期路线验收或完整送达闭环。
- 所有危险字段继续保持 false：`safe_to_control: false`、`delivery_success: false`、`primary_actions_enabled: false`、`robot_control_executed: false`。

## 验收证据

引用 worker report：

- O6 `python3 -m py_compile ...remote_cloud_relay.py`：通过，无输出。
- O6 `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：`Ran 151 tests in 50.374s`，`OK`。
- O6 `git diff --check`：通过，无输出。

Product closeout 轻量验证要求：本目录 `tech-done.md`、`side2side_check.md`、`final.md` 存在；`rg` 可命中 `artifact_bundle`、`software_proof_local_mock_artifact_bundle_ingest_only`、`151 tests`、`O6`；`git diff --check` 通过。

## 收口结论

本 sprint 验收通过，证据边界为 `software_proof_local_mock_artifact_bundle_ingest_only`。O6 可保守上调到约 39%，O7 不上调；本轮不归档 KR。

已更新或待本收口同步更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
