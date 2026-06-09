# O7 Consumer Detail Labeling Queue Pre-Start

## sprint_type

sprint_type: epic

## 1. 启动原因

上一轮 `sprints/2026.06.09_08-09_o7-consumer-detail-route-replay/` 已把 O7 route replay 主路径切到 O6 consumer detail，证明了 `trajectory / events / evidence / labeling / inference / tunnel_status` 这组 consumer-detail 语义可以成为 PC 工作站的主输入。

这轮不再重复做“读模型打通”本身，而是把同一份 consumer-detail 语义继续往 O7 KR4 推进，落到数据标注 / 打标界面的主路径上，让操作员能够在 PC O7 Previews 中做只读标注队列检查，而不是继续停留在 archive fixture 或 labeling fixture 的静态样本浏览。

本轮的产品判断是：**继续推进 O7**，不回头重做 O6。O6 当前仍是最低 Objective，但上一轮已经把 O6 consumer read 变成 O7 可消费的数据入口，因此这轮应优先把这份语义变成用户可见的标注工作流样板，避免 O6/O7 在同一层面重复造轮子。

## 2. 上轮事实和当前证据

- `sprints/2026.06.09_08-09_o7-consumer-detail-route-replay/final.md` 已确认 O7 route replay 主路径切换到 O6 consumer detail，且 build/test/lint/diff-check 通过。
- `sprints/2026.06.09_08-09_o7-consumer-detail-route-replay/tech-done.md` 已确认 consumer-detail 主路径、旧 fixture fallback、fail-closed 文案和只读 cursor 都已经落地。
- `docs/product/pc_tools_workstation.md` 已把 O7 Previews 的 O6 consumer read adapter、route replay、labeling preview、voice preview、safe command preview 边界写清。
- `OKR.md` 4.1 节显示 O6 仍是最低 Objective，但 O7 只有约 5% 进度，当前更适合沿既有 consumer-detail 语义继续推进 O7 KR4，而不是在本轮重新证明 O6 consumer read 本体。

## 3. 本轮方向判断

方向判断：**继续 / 推进 O7 KR4**。

本轮不调整 OKR 方向，不暂停，不替换 Objective。原因是：

1. O6 consumer read 的最小软件链路已经可用，当前更缺的是 O7 面向运营调试的使用方式，而不是重新定义消费契约。
2. labeling / 打标界面天然需要读 `labeling / evidence / events / trajectory` 的同一套 consumer-detail 语义，适合成为 route replay 的下一步。
3. 这轮可以在不改变生产接口的前提下，把“只读标注队列检查视图”做出来，继续积累 O7 用户价值。

## 4. 本轮目标

把 O7 Previews 中的 labeling / 打标能力收敛成一个明确功能点：

- 从 O6 consumer task detail 的 `labeling`、`evidence`、`events`、`trajectory` 摘要构造只读标注队列检查视图。
- 视图只允许检查和复盘，不开放 submit / export / rollback。
- 保留 fail-closed：缺 detail、缺 evidence、缺 labeling、unknown task、blocked/not_proven、危险字段或 schema 不匹配时必须明确关闸。
- 保持与 O7 route replay 一致的 consumer-detail 主路径语义，避免 labeling 重新回到独立 fixture。

## 5. 本轮 owner

- `full-stack-software-engineer`：单 owner，负责 PC workstation 的 labeling queue UI / view model / 测试 / 文档同步。
- `product-okr-owner`：负责需求收口、验收口径、方向判断和 sprint 留档一致性。

## 6. 主要风险

- 如果 labeling 仍停留在 fixture preview，会继续把 O6 consumer detail 的价值压扁成静态样本浏览。
- 如果 submit / export / rollback 的边界不写死，后续很容易把只读检查视图误写成伪交付页面。
- 任何“真实提交成功”“真实导出成功”“真实回滚成功”的文案都必须继续 fail closed，不能因为 UI 完整就抬高能力声明。
