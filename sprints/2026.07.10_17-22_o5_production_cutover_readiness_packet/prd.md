# O5 Production Cutover Readiness Packet PRD

## 用户价值和产品北极星

产品北极星仍是“机器人可以安全、可验证地完成垃圾收取与送达”。O5 的用户价值是让普通手机用户未来能够通过真实公网云中转稳定下发任务、看到状态、在网络或生产依赖异常时得到可理解诊断，而不是依赖本地 relay smoke 或开发者命令行。

本轮核心用户价值是把 O5 从“本地 probe/readback 已经能跑”推进到“production cutover 前还差什么证据一眼可判”：cutover/drain、migration rehearsal、DB/queue external probe、public ingress/TLS、OSS/CDN live traffic、4G/SIM、真实 browser/手机验收这些状态必须进入同一个 O5 readiness packet/readback，并由产品 gate 输出 `okr_credit_allowed`、`support_only_reason` 和 `next_live_command`。

## OKR 映射和方向判断

- 映射 Objective：O5 云中转控制面产品化。
- 方向判断：**继续 O5，并调整抓手到 production cutover readiness packet/readback**。
- 判断理由：
  1. O5 约 85%，是当前最低 Objective；O1 约 87%，O6/O7 约 91%。
  2. `2026.07.10_07-13_o5_o6_live_endpoint_probe_readback` 已把 O5 推到本地 live endpoint probe additive readback，但不是 production proof。
  3. `2026.07.10_08-14_same_task_mission_artifact_credit_gate` 已明确 local/mock probe、readback-only、checklist-only、support-only 不再计主 OKR 增量。
  4. 上一轮 O1 已消费历史真实 same-session wheel feedback material，未连续消费 O5 blocker；本轮回到 O5 符合最低 Objective 路由。
  5. O5 当前真实缺口不再是再写一个 probe wrapper，而是把生产 cutover 所需证据状态收敛成一个可回读、可判 credit、可指向下一条 live command 的合同。

## KR 拆解

本 planning 阶段不归档 KR，也不更新 `OKR.md`。后续 implementation 应推进 O5 当前 KR 的生产化子项：

1. **KR1 commands/status/ack 生产 readiness**：readiness packet 必须消费 cutover/drain 和 worker/migration rehearsal 状态，确认 ACK/terminal result/cursor 语义只是 envelope readiness，不是 delivery success。
2. **KR2 服务端基线规格 readiness**：消费 public ingress/TLS、DNS、reverse proxy、防火墙和公网 health/readiness 外部探测状态。
3. **KR3 OSS 写入策略 readiness**：消费 OSS/CDN live probe、STS 或受限 AK 模式、object ref/hash 摘要和 CDN origin/fetch 状态，不暴露对象 key 或凭证。
4. **KR4 CDN 公开只读入口 readiness**：消费 CDN base rule、origin fetch、public read path 和私有数据隔离状态。
5. **KR5 凭证管理 readiness**：确认所有 evidence intake 只输出脱敏摘要，`.env` 不入仓库，credential-bearing URL/token/AK/SK 均不能进入 packet/readback。
6. **KR6 degradation readiness**：消费 4G/SIM、OSS/CDN、DB/queue、worker/cutover 的 blocked/warning 状态，并输出普通用户可读的 next action 与 `next_live_command`。

## 本轮核心抓手

核心抓手是 `production_cutover_readiness_packet`，不是 review、handoff、状态面板或 another local probe。该 packet 要把既有分散的 O5 gates 聚合成一个产品验收读数：

- 哪些 production evidence classes 已消费；
- 哪些只是 local/software/config-only；
- 为什么当前是否允许 OKR credit；
- 下一条现场或生产命令应该执行什么；
- 哪些 safety/production success flags 必须继续 false。

## 需要做什么

后续 `robot-software-engineer` 需要完成：

- 新增 O5 readiness packet 生成/聚合逻辑，建议 schema 为 `trashbot.o5.production_cutover_readiness_packet.v1`。
- 在 O6 archive/readback 或现有 consumer readback 路径中加入该 packet 的安全摘要和 include 支持，建议 schema 为 `trashbot.o6.production_cutover_readiness_packet_readback.v1`。
- 为以下材料类建立 fail-closed input adapter 或 summary consumer：
  - `cutover_drain`
  - `migration_rehearsal`
  - `db_queue_external_probe`
  - `public_ingress_tls`
  - `oss_cdn_live_probe`
  - `four_g_sim`
  - `browser_phone_acceptance`
- 输出产品 gate 字段：
  - `okr_credit_allowed`
  - `support_only_reason`
  - `next_live_command`
  - `production_external_evidence_classes_consumed`
  - `proof_scope_class`
  - `readiness_blocked_reasons`
  - `delivery_success=false`
  - `safe_to_control=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `production_cutover_success=false`
- 同步更新相关 `docs/` 文档和本 sprint `tech-done.md`；本 planning 子任务只写三份 sprint 计划文档。

## 优先级和验收口径

- 优先级：P0。
- 验收口径：
  1. 能在当前 macOS 环境用本地 fixture/Mock artifact 复验，不依赖真实云凭证才能跑单元测试。
  2. 能对真实外部材料占位和缺失材料做清晰区分：`missing`、`config_present_not_externally_proven`、`external_probe_passed`、`external_probe_failed`、`unsafe_or_unredacted`。
  3. 只有当至少一个新的真实外部 production evidence class 被安全消费，且脱敏自检通过时，才允许 `okr_credit_allowed=true`；否则必须 false。
  4. `okr_credit_allowed=true` 也只代表 production readiness evidence delta，不代表 production cutover success、delivery success 或 safe-to-control。
  5. `support_only_reason` 必须枚举化，不能是自由文本漂移。
  6. `next_live_command` 必须给出下一条可执行生产/现场命令方向，例如 public ingress/TLS probe、DB/queue external probe、OSS/CDN live probe、4G robot outbound polling check、browser acceptance check 或 cutover drain rehearsal。
  7. 所有输出必须通过脱敏规则，不回显 credential、URL、连接串、对象 key、raw response body、本地路径、traceback 或机器人底层控制入口。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- 只读咨询：`full-stack-software-engineer`，仅当 browser/phone acceptance readback 需要 UI/PC 事实补充时介入。
- Product：负责验收口径、OKR credit 判断和收口，不写产品代码。

## 风险、阻塞和需要补齐的证据链

- 真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实手机/browser 验收仍是 O5 主缺口。
- 如果后续实现只消费已有 local/docker/software proof gate，而没有新的真实外部材料，则必须保持 `okr_credit_allowed=false`，本轮只能算 readiness contract / support-only guard，不应提高 O5 百分比。
- 如果输入里出现 credential-bearing URL、Authorization、token、AK/SK、DB endpoint、object key、raw response body、本地路径或 traceback，packet/readback 必须 fail-closed。
- 若真实外部材料不可得，`next_live_command` 必须成为下一轮可执行命令，不允许继续用“等待生产环境”作为唯一结论。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

- 本轮 planning 不移动已完成 KR，不更新 `OKR.md` 历史区。
- 证据来源：
  - `sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/final.md`
  - `sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/final.md`
  - `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/final.md`
  - `OKR.md` 4.1 当前 OKR 进度快照
  - `docs/product/cloud_4g_infrastructure.md`
- 剩余风险：这些证据足以启动 readiness packet 计划，但不足以把 O5 标为 production cloud ready、production cutover success、delivery success 或真实手机/browser 验收完成。

## 需要创建或更新的 sprint 文档

本轮创建：

- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/pre_start.md`
- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/prd.md`
- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/tech-plan.md`

implementation 和收口阶段后续再补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

