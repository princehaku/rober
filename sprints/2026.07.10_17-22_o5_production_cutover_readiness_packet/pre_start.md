# O5 Production Cutover Readiness Packet Pre-start

## sprint_type

sprint_type: epic

## 启动事实

本轮已读取 `AGENTS.md`、`OKR.md`、`docs/product/cloud_4g_infrastructure.md`、最近 O5/O1 sprint 收口文档和自动化 `rober-okr` 记忆。当前 `OKR.md` 4.1 显示：

- O5 云中转控制面约 85%，是当前最低 Objective。
- O1 硬件协议可信底盘约 87%。
- O6 云端核心后端约 91%。
- O7 PC 端运营调试平台约 91%。

最近 `2026.07.10_08-14_same_task_mission_artifact_credit_gate` 已把 local/mock probe、readback-only、checklist-only 和 support-only 工作固定为 `okr_credit_allowed=false`。最近 `2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake` 已消费历史真实上位机 WAVE ROVER same-session wheel feedback material，未连续消费 O5 的同一 local probe blocker。因此本轮可以回到最低项 O5，但不能再做本地 probe wrapper。

## 相关证据

- `sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/final.md`：O5/O6 已能把本地 relay `/healthz`、`/readyz`、`/preflightz` 的 `cloud_external_probe` / `cloud_db_queue_external_probe` 摘要写入同一 `task_id` 并回读，但证据边界仍是 `software_proof_o5_o6_live_endpoint_probe_readback_only`，不证明真实 production cloud、production DB/queue、HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或真实手机/browser。
- `sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/final.md`：`okr_credit_allowed=false` 已成为 hard gate；没有新的 live/field 或 production mission artifact delta 时，后续 O5/O6/O7 工作只能算 support-only 回归守护。
- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/final.md`：上一轮切到 O1 消费历史真实 same-session wheel feedback material，O5 仍保持约 85%，下一轮 O5 只应接真实 production cloud、production DB/queue、live endpoint 或 browser 材料。
- `docs/product/cloud_4g_infrastructure.md`：已有 cloud worker/migration rehearsal、cloud worker cutover/drain、DB/queue external probe、public ingress/TLS、OSS/CDN live probe、4G/SIM external evidence intake 等历史 software-proof gates，但这些分散 gate 仍没有聚合成一个 O5 production cutover readiness packet/readback 合同。

## 本轮目标 Objective

- 主目标：O5 云中转控制面产品化。
- 本轮目标：建立 O5 `production cutover readiness packet/readback` 的产品与验收计划，让后续 `robot-software-engineer` 消费 cutover/drain、migration rehearsal、DB/queue external probe、public ingress/TLS、OSS/CDN live probe、4G/SIM、真实 browser/手机等证据状态，并输出 `okr_credit_allowed`、`support_only_reason`、`next_live_command` 等产品 gate 字段。
- 本轮不是 production cutover success，不是 delivery success，不是再把本地 probe wrapper 记为主 OKR 进度。

## 证据边界

本轮和后续实现必须固定保守边界：

- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `production_cutover_success=false`
- 不证明真实垃圾送达。
- 不证明真实机器人运动。
- 不证明 HIL/hardware safety。
- 不把 ACK、terminal result、drain 或 readiness packet 写成生产成功。

允许承认的事实仅限于：O5 控制面已经把 production cutover 所需外部材料状态聚合成可回读、可脱敏、可 fail-closed 的 readiness packet；若没有真实外部材料，则必须输出 `okr_credit_allowed=false` 和具体 `support_only_reason`。

## Owner

- 主责 owner：`robot-software-engineer`
- 执行方式：单线闭环，由 Robot Software owner 后续负责实现、测试、修复和 `tech-done.md` 留档。
- 咨询 owner：`full-stack-software-engineer` 仅在后续真实 browser/PC 可视化验收需要时补充接口事实，不作为本轮默认并行实现 owner。
- Product / 主节点：只负责产品目标、验收口径、sprint 计划和收口，不写产品代码、不运行实现命令、不修改云端配置。

## 范围约束

本 planning sprint 只创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

本轮 planning 禁止修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `docs/product/`
- 产品代码、测试代码、云端配置、launch 参数或环境变量模板

后续 implementation 若新增合同或接口，必须同步更新相关 `docs/` 文档；本子任务因用户限定文件范围，只在 sprint 计划中记录该要求。

## 验收口径

planning 完成后，后续 implementation 必须做到：

1. 生成一个 O5 production cutover readiness packet/readback 合同，能消费 cutover/drain、migration rehearsal、DB/queue external probe、public ingress/TLS、OSS/CDN live probe、4G/SIM、browser/phone evidence 等枚举状态。
2. 合同输出 `okr_credit_allowed`、`support_only_reason`、`next_live_command`、`production_external_evidence_classes_consumed`、`proof_scope_class` 和固定 false safety flags。
3. 当输入只有 local/mock probe、配置形态、readback-only、checklist-only 或旧 software-proof gate 时，必须 `okr_credit_allowed=false`，并给出明确 `support_only_reason`。
4. 当输入包含真实外部生产材料时，只能把它标为 production readiness evidence delta；仍不得宣称 `production_cutover_success`、`delivery_success` 或 `safe_to_control`。
5. 输出不得泄露 base URL、token、Authorization header、DB/queue endpoint、OSS AK/SK、object key、credential-bearing URL、本地路径、traceback、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

