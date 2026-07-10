# O6 Artifact Seed Media Preflight Final

- sprint_type: epic
- close_time: 2026-07-09 08:35 CST
- product_owner: product-okr-owner
- target_objectives: O6, O7
- evidence_boundary: software_proof_local_mock_media_preflight_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 用户价值和产品北极星

本轮把 O6/O7 从“能提交/导出 local/mock 标注”推进到“能围绕同一 `task_id` 预检 route/replay/keyframe/evidence 的 media 依赖，并把 blocked reasons 与 next required evidence 暴露给 PC 工作台”。运营和开发者现在能更快判断一份现场 artifact seed 是否足以支撑路线回放和标注，而不是等到消费链路末端才发现缺材料。

产品北极星不变：让普通用户把垃圾交给小车后，小车可验证地完成投递。本 sprint 只补 O6/O7 的数据复盘和训练材料可用性预检，不声明真实投递、真实媒体可读、真实机器人控制或真实生产云。

## OKR 映射和方向判断

方向判断：继续 O6/O7，保守上调软件侧进度，不归档 KR。

- O6 从约 36% 保守上调到约 37%。理由：O6 已在同一 `task_id` 主路径补上 `artifact_media_preflight`，覆盖 route/replay/keyframe/evidence 计数、样本 ref、blocked reasons、`local_mock/not_proven` 边界和 O7 固定 consumer section names，并经 `py_compile` 与 `149 tests OK` 证明合同与 fail-closed 行为稳定。
- O7 从约 37% 保守上调到约 38%。理由：O7 已优先消费 O6 `artifact_media_preflight`，缺字段时保守派生 `derived_blocked_not_proven`，并在 route replay / labeling 中展示 media refs、blocked reasons 和 `next_required_evidence`，经 `catalog.test.ts` `204 passed`、`App.test.ts` `247 passed`、build、lint 和 `git diff --check` 证明消费链路稳定。
- 不归档 KR。原因是本轮证据边界仍然是 `software_proof_local_mock_media_preflight_only`：没有真实媒体/OSS/CDN 读写，没有真实 annotation API、真实 dataset export、真实生产云、真实机器人控制，也没有 delivery success 证据。

## KR 拆解、更新或历史归档

- O6 KR2/KR3：task/evidence/read model 继续增强，新增 media preflight 摘要和回读入口。
- O6 KR6：consumer read API 的可用性说明更完整，但仍是 local/mock summary，不是 production read path 完成。
- O7 KR3：路线回放工作台现在能看到 media dependency 与缺口，不再只展示 trajectory/event summary。
- O7 KR4：标注工作台现在能看到当前 media refs、blocked reasons 和 next required evidence，但仍不是真实标注平台完成态。
- 已完成 KR 历史归档：无。本轮不把任何 KR 标为完成或移入历史区。
- 历史记录位置：`docs/process/okr_progress_log.md` 新增 `2026-07-09 07-55｜o6_artifact_seed_media_preflight` 条目。

## 本轮核心抓手

核心抓手是把“现场 artifact seed 是否够用”这件事前移到 O6/O7 主链路，用统一的 `artifact_media_preflight` 合同回答 route/replay/keyframe/evidence 是否齐备、为什么 blocked、下一步需要补什么，而不是继续堆状态字段或只读 wrapper。

## 需要做什么

下一步必须直接消费真实证据链，而不是继续叠加 local/mock surface：

1. 让真实 `route.csv`、replay JSONL、keyframe 或 rosbag 进入 O6 archive，并由 O7 route replay / labeling 主路径消费。
2. 补真实 keyframe/media ref 可访问性 smoke，证明 PC 不是只展示 ref 字符串。
3. 在具备生产 backing 后推进真实 annotation API、真实 dataset export、真实 OSS/CDN 和生产级 archive query。

## 优先级和验收口径

- 当前最高优先级仍是现场 O3 验证 lane，其次 O6、O7。
- O6 下一步验收应要求真实 artifact seed 至少形成一条可复现的 `route.csv`、replay JSONL、keyframe 或 rosbag 消费证据。
- O7 下一步验收应要求真实媒体可访问性或真实 artifact 驱动的回放/标注链路，而不是继续基于摘要或 fallback fixture。
- 本轮验收通过的唯一边界是 `software_proof_local_mock_media_preflight_only`。

## 对应责任 Engineer

- `robot-software-engineer`：O6 archive/read model、artifact media preflight、真实 artifact seed 接入、生产 backing 前置接口。
- `full-stack-software-engineer`：O7 consumer adapter/UI、media dependency 展示、真实 artifact 驱动的回放/标注工作台。
- `robot-algorithm-engineer`：提供 route.csv、replay JSONL、keyframe、rosbag 或现场路线证据，避免 O6/O7 在摘要层自循环。
- `product-okr-owner`：维护保守 OKR 进度、验收边界和 KR 历史归档。

## 风险、阻塞和证据链缺口

- 本轮不证明真实媒体/OSS/CDN、真实 annotation API、真实 dataset export、production cloud、真实机器人控制或 delivery success。
- 不证明 production DB/queue、TLS/4G、真实隧道、真实机器人数据或生产级查询容量。
- 不证明真实 route replay 文件可下载、真实 keyframe 可打开、真实视频/RTC、真实 ASR/TTS、wheel raw 非零、真实电梯状态链、真实长期路线验收或完整送达闭环。
- `artifact_media_preflight` 只是本地/mock media 依赖预检，不是媒体 fetch 成功。

## 验收证据

引用 worker report：

- O6 `python3 -m py_compile ...remote_cloud_relay.py`：通过，无输出。
- O6 `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：`Ran 149 tests in 50.480s`，`OK`。
- O7 `cd pc-tools/workstation && npm run test -- catalog.test.ts`：`Tests  204 passed (204)`。
- O7 `cd pc-tools/workstation && npm run test -- App.test.ts`：`Tests  247 passed (247)`。
- O7 `cd pc-tools/workstation && npm run build`：通过。
- O7 `cd pc-tools/workstation && npm run lint`：通过。

Product closeout 轻量验证要求：三个收口文件存在，`rg` 可命中 `artifact_media_preflight`、`149 tests`、`204 passed`、`247 passed`、`safe_to_control=false`、`delivery_success=false`，并且 `git diff --check` 通过。

## 收口结论

本 sprint 验收通过，证据边界为 `software_proof_local_mock_media_preflight_only`。O6/O7 仅做小幅上调，不归档 KR。

已更新或待本收口同步更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
