# PRD：O7 Mission Evidence Bundle Terminal Material Export

## 需求背景

O7 consumer detail 已能读取 `bounded_route_execution_gate_material` 和 `bounded_route_terminal_result_material`，但 mission evidence bundle export 的 material section 分类仍停留在旧 section 列表。这样会导致 selected-task bundle receipt 没有把最新 gate/terminal material 计入 material summary，影响后续 operator 对同一任务证据链完整性的判断。

## 用户价值

- Operator 导出同一 selected task 的 mission evidence bundle 时，可以看到 O3/O5/O6/O7 近期形成的 bounded route gate 与 terminal result 材料是否被同一条 O6 detail 主路径消费。
- Review 时能区分“材料已进入 bundle receipt”和“真实路线执行/送达仍未证明”，减少人工误判。

## 验收口径

- O7 mission evidence bundle export `section_summaries` 包含 `bounded_route_execution_gate_material` 与 `bounded_route_terminal_result_material`。
- `counts.material_section_count` 把这两个 section 计入 material 类别。
- 现有 fail-closed 行为不放宽：非回环 URL、schema/task mismatch、危险 true 字段、unsafe refs/content 仍失败关闭。
- 文档明确该 export 仍是 local/mock software proof，不证明 production cloud、route execution、delivery success、HIL、safe-to-control 或 real dataset export。

## 非目标

- 不新增 endpoint。
- 不修改 O6 archive 写入语义。
- 不提升 OKR 百分比，不归档 KR。
- 不触发真实控制、Nav2 goal、`/cmd_vel`、`/api/base/manual`、serial/UART 或 WAVE ROVER。
