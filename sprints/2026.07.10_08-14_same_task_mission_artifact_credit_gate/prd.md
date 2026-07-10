# Same-Task Mission Artifact Credit Gate PRD

## 用户价值

产品北极星是可验证地可靠交付垃圾。最近多轮已经有足够的 archive/readback/checklist 能力，但缺口仍停在真实 production cloud、live route execution、delivery record、operator confirmation 和 delivery success。本轮用户价值不是新增一个表面摘要，而是让系统在计划、archive 和 operator 页面里明确区分：

- 哪些 evidence 真正消费了同一 `task_id` 的 mission artifact；
- 哪些 evidence 只是 support-only 回归守护；
- 哪些 sprint 可以计入 OKR 主进度；
- 哪些 sprint 必须保持百分比不变。

## 需求

1. Algorithm manifest 的 same-task mission gate 输出结构化 credit 判定。
2. O6 archive/readback 保留并校验 credit 判定字段，unsafe 或缺字段必须降级为 blocked/support-only。
3. O7 consumer detail 展示 credit gate，不允许把 `okr_credit_allowed=false` 的材料渲染成 mission progress。
4. Product closeout 必须基于 `okr_credit_allowed` 决定是否更新 OKR 百分比。

## 非目标

- 不接入真实 production cloud、DB/queue、TLS、4G 或 OSS/CDN。
- 不新增真实机器人运动或硬件控制。
- 不把历史材料包装成新的 delivery success。
- 不修改 WAVE ROVER vendor 协议、UART 参数或真实硬件配置。

## 验收标准

- Algorithm unit test 覆盖 ready gate 下的 `okr_credit_allowed=true` 条件，以及 probe/checklist/readback-only 下的 `okr_credit_allowed=false`。
- O6 relay test 覆盖 archive detail、field evidence、consumer include 回读中的 credit fields。
- O7 test/build/lint 通过，UI/adapter 能展示 credit gate 状态。
- Sprint `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。
- `OKR.md` 和 `docs/process/okr_progress_log.md` 同步写明本轮是否提高百分比；若只交付 gate，则通常不提高或只写流程硬化，不宣称 mission success。

## 风险边界

本轮最多证明 same-task mission artifact credit gate 的软件可执行性。它不证明真实 production cloud、真实 live route execution、真实 robot motion、真实 delivery record、operator confirmation、真实 WAVE ROVER L/R 非零反馈或真实 delivery success。
