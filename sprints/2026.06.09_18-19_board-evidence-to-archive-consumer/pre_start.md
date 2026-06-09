# 预研启动 - 板载 Evidence 到 O6 Archive / O7 Consumer Detail

## sprint_type

`sprint_type: epic`

## 本轮背景

- `HEAD` 与 `origin/master` 当前为 `ce68415`（`Add O7 field evidence consumer ingest`）。
- 先前两轮现场取证主要因 `ssh root@192.168.1.11 -p 37878` 不可达而阻塞；本轮不允许再次将“同一 SSH blocker”作为唯一验收。
- 上一轮 `field evidence manifest` 已完成到 `trashbot.field_evidence_manifest.v1` 产物，现需继续把这条产物接入 `O6` 存档与 `O7` consumer detail，形成可验证软件链路。
- 设计约束：如果 SSH 不可达，必须能用 local/mock 继续验证功能完整性并产出软件证据。

## 用户价值与北极星

当前目标是把“现场材料文件”从一个孤立的 artifact gate，变成可被 O6/O7 联动消费的数据链路入口。  
北极星不变：让用户任务可持续被记录、可复盘、可消费，不以“等待现场可达”为阻断。

## OKR 映射与方向判断

- 当前最低完成度 Objective（来自 `OKR.md`）仍为 **O7（~12%）**，同时 O6 仍需向下沉淀到可消费的数据链路。
- 本 sprint 方向：**继续推进且不降档（continue）**，聚焦两条价值：
  - O7：让 PC/移动端可从 `field_evidence_manifest.v1` 看到消费来源、`manifest gate` 与 `artifact_status` 的统一摘要，并驱动 route/replay / labeling 前置数据。
  - O6：把 manifest 作为 O6 archive / consumer 入口，避免 `manifest` 停在边界文件里无法转化为任务证据链。
- 不再把主线定义为“现场 SSH 可达即闭环”；SSH 仅作为增强路径，不是本轮唯一前置。

## KR 拆解（本轮）

- `O7-KR3（历史路线回放）`：
  - 要求 manifest -> consumer detail 的消费链，route replay 通过同一 task 语义读取轨迹/关键帧/状态样本。
- `O7-KR4（数据打标）`：
  - 要求 manifest 可带入 labeling/审阅队列 mock 入口，便于后续标注闭环接管。
- `O6-KR2 / O6-KR6`（任务记录与consumer read）：
  - 要求 manifest 可映射到 O6 archive task 轨迹与事件；并能在 `consumer detail` 中看到来源与边界。
- `O6-KR3` 补充：
  - 要求 evidence_ref 等关键指纹被保留，不让数据成为 orphan artifact。

## 本轮范围

### 本轮明确不做

- 不证明真实 4G/公网/HIL/送达，默认只做软件侧闭环。
- 不改 `docs/vendor/` 事实，不改 WAVE ROVER、ESP32、串口、UART、波特率、速度映射等硬件细节。
- 不进行机器人真机控制动作、Nav2 实跑、真实控制下发。

### 实施前置范围（给实现 owner）

- `onboard/scripts/field_route_evidence_preflight.py`（读取 gate 状态）
- `onboard/scripts/field_route_evidence_manifest.py`（manifest 输入口）
- `onboard/tests/test_field_route_evidence_manifest.py`（本地 manifest smoke）
- `pc-tools/workstation/src/server/**`（manifest -> O6 archive / consumer detail 适配）
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`（入口与摘要展示）
- `pc-tools/workstation/test/**`
- 视需要补充 `docs/navigation/field_route_evidence_manifest.md`、`docs/navigation/o7_field_evidence_consumer_ingest.md`、`docs/product/pc_tools_workstation.md` 的同步说明

## 交付原则

- 按“Manifest 先行 + fail-closed 兜底”发布：即便 SSH 不可达，仍必须产出完整的 `not_proven / delivery_success=false / primary_actions_enabled=false` 软件证据摘要。
- 一次设计可直接指导下一位 `full-stack-software-engineer` 起步，不保留“再澄清字段/字段含义”的空缺。

## 当前阻塞与缓解

- **可能阻塞**：SSH 仍不可达时 manifest 的 real artifact 更新无法实时拉下；已定义为不阻塞软件实现，改为本地 fixture 继续验收。
- **剩余边界**：字段来源与 O6 存档 schema 的兼容边界需实现时再冻结（本轮仅设计）。

