# Same-Task Mission Artifact Credit Gate Side-to-Side Check

## 对照范围

- 计划基线：`pre_start.md`、`prd.md`、`tech-plan.md`
- 工程交付：Algorithm / O6 / O7 三个 worker 已完成的代码、测试和文档结果
- Product 收口目标：确认本轮是否允许提高 O5/O6/O7 百分比，以及是否把 support-only 工作错误记成 mission 主进度

## Side 1：计划承诺

1. `same_task_mission_evidence_gate` 必须新增 `same_task_id_consumed`、`mission_artifact_delta`、`live_or_field_command_executed`、`support_only_reason`、`okr_credit_allowed`。
2. local/mock/readback-only/probe-only/checklist-only 输入必须 fail-closed 为 `okr_credit_allowed=false`。
3. Product closeout 需要据此决定本轮是否允许调整 O5/O6/O7 百分比。

## Side 2：实际交付

1. Algorithm 已在 manifest 侧补齐结构化 `mission_artifact_delta` 和 credit gate 字段，验证 `Ran 60 tests in 0.313s OK`。
2. O6 已在 archive/readback 侧回读并保留 credit fields，验证 `Ran 168 tests in 64.612s OK`。
3. O7 已在 consumer/UI 侧展示 credit fields，并把 `okr_credit_allowed=false` 收紧为 support-only/blocked 语义，验证 `Tests 484 passed (484)`、build、lint 通过。
4. `OKR.md` / `docs/process/okr_progress_log.md` 将本轮明确写成 hard gate / credit gate 软件合同，不提高 O5/O6/O7 百分比。

## 验收判断

- 计划承诺 1：满足。字段已在 Algorithm、O6、O7 三层串通。
- 计划承诺 2：满足。worker 结果明确说明 support-only、缺字段、legacy unstructured delta、unsafe text、dangerous true、task mismatch 均 fail-closed。
- 计划承诺 3：满足。Product 收口结论是不调 O5/O6/O7 百分比。

## 差异与解释

- 本轮没有新增真实/准现场 mission artifact delta，因此虽然合同支持 `okr_credit_allowed=true`，但这不是本轮主验证场景。
- 结果上，本轮更像“防止误加分”的硬化 sprint，而不是“新增 mission 成功证据”的推进 sprint。

## 收口结论

本轮 side-to-side 一致。用户价值在于把 support-only 工作从主 OKR 增量里剥离，避免 O5/O6/O7 因 probe/checklist/readback-only 包装而继续虚增。
