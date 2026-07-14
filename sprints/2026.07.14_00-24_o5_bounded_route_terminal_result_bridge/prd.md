# PRD - O5 Bounded Route Terminal Result Bridge

## 用户价值

普通用户只关心手机任务是否已经被云端接收、机器人是否上报了终态、以及该终态是不是可相信的送达结果。本轮把已有 same-task bounded route mock execution 材料接入 O5 terminal-result/reconciliation 主路径，让云端控制面可以对任务级结果做本地可验证闭环，同时继续把真实送达和软件终态分开。

## OKR 对齐

- Objective: O5 云中转控制面产品化。
- 当前进度：约 `85%`。
- 本轮推进点：不是继续做外部证据包装，而是把 O5 phone command、robot terminal result 和 result reconciliation 主链路串成同一任务的软件证明。
- 不调整 KR 完成状态：本轮若只得到 local/mock artifact，O5 百分比原则上保持 flat，除非 Product closeout 明确判断 terminal-result bridge 是新的可计分软件主链路增量。

## 需求范围

必须实现：

- 新增本地 CLI bridge，默认消费 `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json`。
- Bridge 生成 schema 为 `trashbot.o5.bounded_route_terminal_result_bridge.v1` 的 summary artifact。
- Bridge 必须调用既有 O5 relay 主路径，不绕过接口直接写 store：
  - `POST /api/commands/collect`
  - `POST /robots/{robot_id}/commands/{command_id}/terminal-result`
  - `GET /api/commands/{command_id}/result?robot_id=...`
- Artifact 必须保留同一任务 identity：
  - `task_id`
  - `packet_id`
  - `route_intent_id`
  - `route_csv_row_count`
  - `segment_count`
  - `progress_jsonl_event_count`
- Artifact 必须固定 false fields：
  - `delivery_success=false`
  - `route_execution_success=false`
  - `safe_to_control=false`
  - `hil_pass=false`
  - `robot_control_executed=false`
  - `connects_cloud_production=false`
  - `uses_base_uart=false`
  - `publishes_cmd_vel=false`
  - `calls_base_manual=false`

不得实现：

- 不接真实公网、真实 DB/queue、OSS/CDN、4G/SIM。
- 不触发真实机器人控制、Nav2 action、`/cmd_vel`、`/api/base/manual` 或 UART。
- 不新增 UI surface 或 O6/O7 wrapper。
- 不把 mock execution terminal result 声明成真实送达成功。

## 验收口径

Product 接受：

- 同 task bounded route mock execution summary 被 O5 terminal-result bridge 消费。
- Command enqueue、terminal result record、result reconciliation 均由 HTTP 主路径完成。
- Summary artifact 机读可复核，危险字段全部 false。
- 单测覆盖 happy path、identity mismatch、dangerous true field / unsafe payload fail-closed。

Product 拒绝：

- 真实 route execution。
- 真实 delivery success。
- production cloud / production DB/queue。
- HIL / safe-to-control。
- O5 external production evidence。

## 下一步证据

如果本轮通过，下一轮 O5 仍只能通过 success-class production/external evidence 继续提升；否则转向 explicit-operator-approved current live HIL/current route execution/delivery/operator evidence。
