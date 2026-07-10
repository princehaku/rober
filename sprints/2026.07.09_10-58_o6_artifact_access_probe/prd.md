# O6 Artifact Access Probe PRD

## 用户价值和产品北极星

用户最终需要的是：把垃圾交给小车后，后端能保存并复盘“这次任务为什么能送达或为什么失败”。O6 的 archive/read model 如果只保存字符串 ref，运营和工程无法判断 ref 背后的 `route.csv`、replay JSONL、keyframe 或 rosbag 是否真的存在、是否可读、大小是否合理、是否能作为后续 O7 回放/标注入口。

本轮用户价值是把“看见 artifact ref”推进到“安全证明 artifact ref 至少可被本地/mock 受限探测”。这不是送达闭环完成态，但能直接减少下一步 O7 回放、标注和训练数据准备中的假阳性。

产品北极星不变：让普通用户把垃圾交给小车后，小车可验证地完成垃圾投递。本轮只补可复盘数据底座，不声明真实投递、真实机器人控制或真实生产云。

## OKR 映射和方向判断

方向判断：继续 O6，O7 作为 secondary consumer。

- O6 当前约 39%，是 active Objective 中最低进度；本轮直接针对 O6 KR2/KR3/KR6。
- O7 当前约 40%，本轮只在 O6 probe 结果稳定后读取并展示 readiness，不新增独立 O7 wrapper。
- 不暂停、不替换 OKR；原因是最近 sprint 没有被不可解外部 blocker 卡死，而是已经具备 artifact bundle / readiness 软件底座，下一步应消费 artifact seed 的可访问性证据。

## KR 拆解、更新或历史归档

- O6 KR2：任务记录和感知事件需要能关联可探测的路线/回放/关键帧/证据引用。本轮补 `artifact_access_probe` 摘要，让 archive detail 不只保存字符串。
- O6 KR3：大对象仍不入库，只保存 refs 与安全摘要；sha256/size/type 是对本地/mock artifact 的可复现摘要，不替代 OSS 存储。
- O6 KR6：consumer read API 应在同一 `task_id` 下回读 probe 摘要，供 PC 端和手机端后续消费。
- O7 KR3/KR4：只有在 O6 probe 可回读后，才允许展示 route replay / labeling readiness 的可访问性状态。
- 已完成 KR 历史归档：无。本轮计划阶段不把任何 KR 标为完成，也不修改 `OKR.md`。

## 本轮核心抓手

核心抓手是 `artifact access probe`：在受限本地/mock 范围内读取 artifact bundle 或 field evidence 的本地 refs，产出存在性、大小、sha256、类型和阻塞原因摘要，并通过 O6 archive/read 主路径回读。

## 需要做什么

1. 为 O6 增加安全 probe 合同，输入来自现有 artifact bundle / field evidence 的本地 refs 或测试 fixture refs。
2. 对允许的相对 ref 做只读探测，生成 `exists`、`size_bytes`、`sha256`、`detected_type`、`blocked_reason` 等摘要。
3. 对危险 ref fail-closed，包括 token URL、credential URL、绝对路径、父目录逃逸、raw/base64、过大文件或不在 allowlist root 内的路径。
4. 将 probe 摘要写入同一 `task_id` 的 archive task detail / consumer detail。
5. O7 如参与，只读取 O6 probe 摘要并展示 readiness，不新建与 O6 分离的事实来源。

## 优先级和验收口径

优先级：

1. P0：O6 安全 probe、fail-closed、archive/read 回读和测试。
2. P1：O6 接口文档同步，说明 local/mock/not_proven 边界。
3. P2：O7 secondary readiness 展示，只有在 O6 probe 合同稳定后执行。

验收口径：

- 至少一个安全 fixture ref 被探测并回读 `exists=true`、非空 `sha256`、`size_bytes` 和 `detected_type`。
- 至少一个危险或不可访问 ref 被 blocked，并提供可读 `blocked_reason`。
- O6 单元测试覆盖 happy path、missing file、unsafe ref 和 consumer detail readback。
- O7 如参与，测试覆盖 probe readiness 展示和 `not_proven`/blocked 状态，不允许显示真实生产可用。
- 文档明确本轮证据边界是 `software_proof_local_mock_artifact_access_probe_only`。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- 次责：`full-stack-software-engineer`
- 事实补充：`robot-algorithm-engineer`
- 产品验收：`product-okr-owner`

## 风险、阻塞和需要补齐的证据链

- 真实 artifact 可访问性仍取决于后续现场材料：真实 `route.csv`、replay JSONL、keyframe、rosbag 或真实 evidence seed。
- 本轮不触碰生产凭证，不验证 OSS/CDN，不验证公网隧道、production DB/queue、TLS/4G 或生产容量。
- 本轮不证明真实媒体可播放、真实 annotation API、真实 dataset export、真实 RTC/视频、真实 ASR/TTS、wheel raw 非零或 delivery success。
- 后续必须补一轮真实或离线 artifact seed smoke，至少把一个现场文件放入 allowlist root 并验证 O6/O7 可消费。

## 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现阶段必须新增：`tech-done.md`，记录实际改动、验证结果和剩余风险。
- 收口阶段必须新增：`side2side_check.md`、`final.md`，并在有证据后再判断是否更新 `OKR.md` 和历史记录。
