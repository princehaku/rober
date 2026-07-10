# O7 Artifact Bundle Consumer Readiness Final

- sprint_type: epic
- close_time: 2026-07-09 10:48 CST
- product_owner: product-okr-owner
- target_objective: O7 PC 端运营调试与数据训练平台
- secondary_objective: O6 consumer compatibility only
- evidence_boundary: software_proof_local_mock_artifact_bundle_consumer_readiness
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 用户价值和产品北极星

本轮把 O7 从“能消费 O6 的 bundle 相关摘要”推进到“PC 端 consumer detail 主路径可以直接看见 `artifact_bundle_readiness`，并据此判断材料是否可用、哪里被阻塞、下一步缺什么证据”。这让运营和开发者在同一 `task_id` 下不必手工拼接多个 wrapper，也能更快决定是否继续回放、标注或等待补证据。

产品北极星不变：让普通用户把垃圾交给小车后，小车可验证地完成投递。本 sprint 只补 O7 的 consumer readiness 软件侧闭环，不声明真实投递、真实机器人控制、真实媒体可读或真实生产云。

## OKR 映射和方向判断

方向判断：继续 O7，保守上调软件侧进度；O6 维持当前水平，不归档 KR。

- O7 从约 38% 保守上调到约 40%。理由：本轮明确补齐 `artifact_bundle_readiness` 主路径，`o7ConsumerReadAdapter.ts`、`contracts.ts`、`O7FixturePreviewPanel.vue` 以及测试/文档都已同步，且 worker 记录 `npm run test` 通过 `470 passed`、`npm run build` 通过、`npm run lint` 通过。
- O6 维持约 39%。理由：本轮没有新增 O6 写入能力，只是消费 O6 已有 bundle / ingest / preflight 结果。
- 本轮不归档 O7 KR3/KR4。当前仍是 software proof / local mock 边界，没有真实生产云、真实媒体、真实 annotation API、真实 dataset export、真实 RTC/视频、真实 ASR/TTS 或真实机器人运动证据。

## KR 拆解、更新或历史归档

- O7 KR3：历史路线回放从局部 mock 视图继续前进到统一的 `artifact_bundle_readiness` 消费视图，但仍不是真实生产回放完成态。
- O7 KR4：数据标注界面继续前进到与 O6 bundle 联动的可用性判断，但仍不是真实标注平台完成态。
- O6 只作为 consumer compatibility 的 secondary objective，没有新增写入入口或生产数据底座。
- 已完成 KR 历史归档：无。本轮不把任何 KR 标为完成或移入历史区。
- 历史记录位置：`docs/process/okr_progress_log.md` 新增 `2026-07-09 09-57｜o7_artifact_bundle_consumer_readiness` 条目。

## 本轮核心抓手

核心抓手是把 O7 consumer detail 的判断从“看见一些局部摘要”提升到“明确看见同一 `task_id` 下的 `artifact_bundle_readiness`”，并把 blocked reasons、next required evidence 和样本 refs 变成面向运营的直接信号。

## 需要做什么

下一步必须直接消费真实证据链，而不是继续叠加 local/mock readiness surface：

1. 让真实 `route.csv`、replay JSONL、keyframe 或 rosbag 进入 O6 archive，并由 O7 主路径消费。
2. 补真实 keyframe / media ref 可访问性 smoke，证明 PC 不是只展示字符串引用。
3. 在具备生产 backing 后推进真实 annotation API、真实 dataset export、生产级 archive query 和长期数据回灌。

## 优先级和验收口径

- 当前最高优先级仍是现场 O3 验证 lane，其次 O6、O7。
- O7 下一步验收应要求真实 artifact 驱动的回放或标注消费链路，而不是继续只依赖 local/mock readiness 摘要。
- O6 下一步验收应要求真实 artifact 至少形成一条可复现的 `route.csv`、replay JSONL、keyframe 或 rosbag 消费证据。
- 本轮验收通过的唯一边界是 `software_proof_local_mock_artifact_bundle_consumer_readiness`。

## 对应责任 Engineer

- `full-stack-software-engineer`：负责 O7 consumer readiness、UI 展示、adapter 和相关测试/文档。
- `robot-software-engineer`：负责 O6 archive/read model、artifact bundle / preflight 的兼容消费边界。
- `robot-algorithm-engineer`：负责提供 route.csv、replay JSONL、keyframe、rosbag 或现场路线证据，避免 O7 继续在摘要层自循环。
- `product-okr-owner`：维护 O7/O6 的保守进度、验收边界和 KR 历史归档。

## 风险、阻塞和证据链缺口

- 本轮不证明真实媒体/OSS/CDN、真实 annotation API、真实 dataset export、production cloud、真实机器人控制或 delivery success。
- 不证明 production DB/queue、TLS/4G、真实隧道、真实机器人数据或生产级查询容量。
- 不证明真实 route replay 文件可下载、真实 keyframe 可打开、真实 RTC/视频、真实 ASR/TTS、wheel raw 非零、真实电梯状态链、真实长期路线验收或完整送达闭环。
- `artifact_bundle_readiness` 只是 local/mock consumer readiness，不是生产可用性证明。

## 验收证据

引用 worker report：

- `npm run test -- --runInBand`：失败，原因是 Vitest 不支持该参数。
- `npm run test`：成功，结果 `3 passed`、`470 passed`。
- `npm run build`：成功。
- `npm run lint`：成功。
- `git diff --check`：成功。

## 收口结论

本 sprint 验收通过，证据边界为 `software_proof_local_mock_artifact_bundle_consumer_readiness`。O7 可保守上调到约 40%，O6 维持约 39%；本轮不归档 KR。

已更新或待本收口同步更新：

- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

