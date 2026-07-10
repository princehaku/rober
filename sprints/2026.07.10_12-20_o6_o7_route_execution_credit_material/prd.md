# O6/O7 Route Execution Credit Material PRD

## 用户价值

运营人员和 Product 需要判断同一 `task_id` 的 route execution material 是否只是可读摘要，还是已经包含 live/field command evidence 与 delivery/operator record material。当前 O7 可以看到 packet ready，但仍需要人工跨多个 section 推断它是否允许计入主 OKR credit。

本轮要把这个判断做成 Algorithm -> O6 -> O7 的稳定字段，并保持所有真实成功、安全控制和生产云声明为 false/not proven。

## 目标

1. `same_task_route_execution_material_packet` 新增 credit-aware material 字段：
   - `live_or_field_command_evidence_present`
   - `delivery_or_operator_material_consumed`
   - `route_execution_credit_candidate`
   - `credit_support_only_reason`
   - `credit_required_evidence`
2. O6 archive/readback 保留这些字段，坏 schema、task mismatch、unsafe text、dangerous true 或缺字段必须 fail-closed。
3. O7 consumer/UI 展示 packet credit material summary，并把 `route_execution_credit_candidate=false` 显示成 support-only/blocked。

## 非目标

- 不新增真实生产云探测。
- 不新增真实硬件控制或 HIL 准入。
- 不把 `route_execution_credit_candidate=true` 解释成 `delivery_success=true`。
- 不把 local/mock fixture 自动计入 O5/O1 进度。

## 验收口径

- Algorithm 单测覆盖 ready credit candidate、缺 delivery/operator material、缺 live/field evidence、unsafe linked summary。
- O6 单测覆盖 archive detail、consumer include、field evidence/artifact bundle 回读和 fail-closed。
- O7 单测覆盖默认 include/detail 展示、support-only 文案和 dangerous true fail-closed。
- 文档同步更新 `docs/navigation/field_route_evidence_manifest.md`、`docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md` / `docs/interfaces/o7_realtime_operator_console.md`。

## OKR 预期

本轮若三层链路通过，O6/O7 可从 `~87%` 保守推进到 `~88%`：原因是 route execution material 从“可回读 packet”提升为“可判断 mission credit material 的 same-task packet”。O5/O1 不调整。
