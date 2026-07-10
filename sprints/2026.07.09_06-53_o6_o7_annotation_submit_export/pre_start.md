# O6/O7 Annotation Submit Export Pre Start

## sprint_type: epic

- automation_id: rober-okr
- start_time: 2026-07-09 06:53 Asia/Shanghai
- product_owner: product-okr-owner
- target_objectives: O6 云端核心后端, O7 PC 端运营调试与数据训练平台
- primary_boundary: software_proof_local_mock_annotation_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 背景和上轮事实

最近两轮已经把 O6/O7 的本地数据链路推进到可读但不可写的边界：

- `sprints/2026.07.09_02-31_o6_field_evidence_archive_ingest/` 已完成 O6 field evidence local/mock archive ingest，证据边界为 `software_proof_local_mock_archive_only`。O6 能接收 `field_evidence_manifest` 并让 O7 consumer read 回读 `field_evidence` wrapper，但不证明真实生产云、OSS/CDN、TLS/4G、真实路线或真实机器人数据。
- `sprints/2026.07.09_05-51_o7_route_replay_labeling_mvp/` 已完成 O7 consumer detail 主路径的 `route_replay_mvp` 与 `labeling_mvp` 展示，证据边界为 `software_proof_local_mock_consumer_only`。PC 能围绕同一 `task_id` 展示 review item、draft labels、schema 和 `submit_blocked_fail_closed`，但仍没有真实 annotation submit、dataset export 或媒体可访问性闭环。

两轮 `final.md` 都要求下一轮避免 wrapper-only / surface-only，优先推进真实 route artifacts、媒体可访问性，或 annotation submit/export 最小链路。本轮选择不重复硬件、camera、wheel raw blocker 的 O6/O7 交界项：local/mock annotation submit + dataset export。

## 用户价值和产品北极星

用户价值是让运营/开发者在 PC 工作站看到一条任务材料后，能把本地/mock 标注真正提交到 O6 archive，并导出任务级训练数据摘要。这样 `route.csv`、replay JSONL、keyframe refs 和 labeling draft 不再停在只读预览，而是形成可复盘、可回灌、可测试的最小数据闭环。

产品北极星保持不变：让普通用户把垃圾交给小车后，小车可验证地完成投递。本 sprint 只补数据训练与复盘链路，不声明真实投递、真实控制、真实生产云或真实机器人运动。

## OKR 映射和方向判断

- 方向判断：继续 O6，同时协同 O7。
- O6 当前约 33%，是当前最低活跃 Objective；本轮直接补 O6 KR4 标注 API 和 KR6 consumer read 的写入/导出缺口。
- O7 当前约 34%；本轮协同补 O7 KR4 数据标注/打标界面的 submit/export 最小链路。
- 本轮不调整 O1/O5，也不重新消费 WAVE ROVER、camera、wheel raw、4G/TLS 或生产云 blocker。
- 本轮不把任何 KR 标为完成；只有在 implementation 产生 submit/export 单测、PC 测试、build/lint 和 diff check 证据后，才允许在 `side2side_check.md` / `final.md` 里判断是否保守上调 O6/O7。

## 本轮核心抓手

核心抓手是把上一轮 `submit_blocked_fail_closed` 从纯展示态推进为 local/mock 可提交、可持久化、可导出的数据闭环，同时保留真实能力 fail-closed：

- O6 backend 接收 PC 提交的标注 payload，写入 file-backed local/mock archive store。
- O6 backend 提供 task 级 annotation dataset export 响应，返回安全摘要和可复现 manifest，不回显绝对路径、凭证、base64、原始大对象或任何控制字段。
- O7 PC consumer detail 主路径增加 local/mock submit/export 触发和结果展示，继续只允许本机回环 relay base URL。
- 所有真实能力字段继续 false：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`connects_cloud_production=false`、`real_annotation_api_connected=false`、`real_dataset_export_connected=false`。

## Owner 和职责

- `robot-software-engineer`：负责 O6 backend/local mock API、store、Python tests、O6 interface docs。
- `full-stack-software-engineer`：负责 O7 PC adapter/UI/client/contracts/tests、PC docs。
- `product-okr-owner`：负责本 epic 后续 `tech-done.md` 核对、`side2side_check.md`、`final.md`、OKR 判断和历史证据归档；本 planning 任务不改 `OKR.md`。

## 范围边界

### In Scope

- local/mock annotation submit 到 O6 archive store。
- task 级 annotation dataset export 的 local/mock API 与安全响应。
- PC O7 consumer detail 主路径触发 submit/export，并显示 receipt/export result。
- Python unittest、PC catalog/App tests、build、lint、git diff check 作为软件侧验收。
- 相关 `docs/` 和 `pc-tools/README.md` 在 implementation 阶段同步更新。

### Out of Scope

- 真实生产 DB/queue、OSS/CDN、TLS/4G、公网云、真实 STS 凭证。
- 真实机器人控制、Nav2 下发、WAVE ROVER 串口、`/cmd_vel`、电梯/路线实跑。
- 真实 camera/RTC/video、ASR/TTS、wheel raw 非零、delivery success。
- 本 planning 任务不运行 implementation 验收命令，不修改产品代码、测试代码、`OKR.md` 或既有 `docs/`。

## 风险和阻塞

- 当前 O6 labels API 已有 local/mock submit 基础，但上一轮 O7 主路径仍固定展示 `submit_blocked_fail_closed`；implementation 需要明确区分“local/mock archive write proof”和“真实 annotation API 连接”。
- `dataset_export_available` 在旧合同中是危险字段，不能直接改为 true。应新增或复用 local/mock 专用字段表达导出已生成，例如 `local_mock_dataset_export_written=true` / `dataset_export.status=local_mock_export_ready`，同时保持 `dataset_export_available=false`。
- PC UI 增加 submit/export 触发时，不得把它放到普通用户首屏或机器人控制面板；只能在 O7 consumer/detail 标注工作台内通过本机回环 adapter 调用。
- 若 backend 与 PC 合同不一致，优先保持旧 O6/O7 字段向后兼容，只新增 optional 字段，不删除上一轮 `route_replay_mvp` / `labeling_mvp` / `submit_receipt` 字段。

## 需要创建或更新的 sprint 文档

- 本 planning 任务创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- implementation 完成后必须更新：`tech-done.md`。
- product 收口时必须更新：`side2side_check.md`、`final.md`。
