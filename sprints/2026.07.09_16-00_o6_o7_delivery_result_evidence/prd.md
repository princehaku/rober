# O6/O7 Delivery Result Evidence PRD

## 用户价值

普通用户最终关心的是“垃圾是否已被安全送到/交付”。当前 O6/O7 已能展示路线、field motion、Nav2 goal execution 等软件证据，但送达结果仍停留在 `next_required_evidence` 字符串。把 delivery result 变成结构化证据后，PC 端可以明确告诉运营人员：当前任务是否已有送达结果记录、记录来自哪里、哪些字段仍不能证明真实送达、下一步该补人工确认还是现场 delivery record。

## OKR 对齐

- O6 KR2/KR6：任务记录和事件/证据存档继续增强，consumer read 可以围绕同一 `task_id` 回读 delivery result evidence。
- O7 KR3/KR4：历史路线回放和标注工作台可看到 delivery result readiness，知道是否能进入投放确认或仍需补证。

## 需求范围

1. Algorithm 支持可选 `--delivery-result-json` 输入：
   - 缺失时输出 `blocked_not_proven` 同形占位。
   - 安全 JSON 只提取白名单字段，生成 `trashbot.delivery_result_evidence.v1`。
   - 证据写入 manifest 顶层和 `field_motion_evidence_packet.delivery_result_evidence`。

2. O6 local/mock archive 支持 readback：
   - `POST /api/o6/archive/field-evidence` 与 `POST /api/o6/archive/artifact-bundle` 可接收该 additive 摘要。
   - archive task detail、field evidence、artifact bundle、consumer detail 和 `include=delivery_result_evidence` 可回读。
   - 对坏 schema、危险 true、路径/root/token/raw/base64、unsafe text 统一 fail-closed。

3. O7 consumer detail 支持展示：
   - 读取 O6 顶层 alias、field evidence、field motion packet、artifact bundle、artifact bundle readiness 中的 `delivery_result_evidence`。
   - UI 展示 status、proof scope、record source、operator confirmation、blocked reasons、next evidence 和 false safety flags。
   - 任何危险成功/控制声明导致 detail fail-closed，不回显危险内容。

## 非目标

- 不证明真实 delivery success。
- 不连接 production DB/queue、OSS/CDN、TLS/4G 或真实云。
- 不执行 `/cmd_vel`、Nav2 goal、manual control、keyboard control、delivery complete submit 或任何真实底盘动作。
- 不把 mock/operator claim 升级为普通用户可见的“已完成投递”。

## 验收口径

- Algorithm 单元测试覆盖 ready、missing、schema mismatch、dangerous true/unsafe text。
- O6 单元测试覆盖 field-evidence/artifact-bundle ingest、consumer include、missing/unsafe fail-closed。
- O7 测试覆盖 consumer detail 展示、artifact bundle readiness 汇总、UI 文案/DOM、unsafe fail-closed。
- 文档同步更新 `docs/navigation/field_route_evidence_manifest.md`、`docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`。

