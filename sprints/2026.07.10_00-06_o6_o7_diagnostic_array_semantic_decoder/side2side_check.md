# O6/O7 DiagnosticArray Semantic Decoder Side2Side Check

## Sprint 类型

sprint_type: epic

检查时间：2026-07-10 00:34 CST。

## 用户价值和产品北极星

产品北极星仍是让普通手机用户可验证地完成低成本垃圾投递；O6/O7 的价值是把路线、诊断和送达证据沉淀成普通运营人员能读、能复盘、能判断下一步的材料。本轮把 DiagnosticArray 从 unsupported 转成 decoded 摘要，让 route bag 中的诊断状态、最高等级和诊断来源样本能被 O6/O7 安全展示，减少运营人员只能看到“缺 decoder”的盲点。

## PRD 对照

| PRD 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Algorithm 支持 `diagnostic_msgs/msg/DiagnosticArray` 安全 decoder | 通过 | `algorithm_worker_report.md`：`decode_diagnostic_array_payload`、`diagnostic_array_summary`，`Ran 48 tests in 0.236s OK` |
| Full semantic decode matrix 输出 DiagnosticArray decoded item | 通过 | Algorithm report 与 O6/O7 report 均记录 `status=decoded`、`decoder_name=decode_diagnostic_array_payload` |
| O6 archive/readback/include 保留 decoded matrix item | 通过 | `o6_worker_report.md`：field evidence、artifact bundle、archive detail、consumer detail、explicit include 均覆盖，`Ran 163 tests in 60.706s OK` |
| O7 consumer/UI fixture 展示 DiagnosticArray decoded coverage | 通过 | `o7_worker_report.md`：`/diagnostics`、`diagnostic_msgs/msg/DiagnosticArray`、`decode_status=decoded` 可见，`482 passed`、build、lint 通过 |
| false safety flags 继续 fail-closed | 通过 | 三个 report 均保留 `safe_to_control=false`、`delivery_success=false` 或对应 false actions |
| 文档同步 | 通过 | worker report 记录更新 `docs/navigation/field_route_evidence_manifest.md`、`docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`、`pc-tools/README.md`；Product 收口同步 `OKR.md` 与 `docs/process/okr_progress_log.md` |

## 与上一轮对照

上一轮 `sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/` 已让 `nav_msgs/msg/Odometry` 在 semantic replay 和 full matrix 中 decoded，O6/O7 约 76%。本轮新增的是 DiagnosticArray decoder 覆盖：`diagnostic_msgs/msg/DiagnosticArray` 从 unsupported topic type 转为 decoded，并让 O7 fixture `coverage_ratio=1`、`unsupported_topic_type_count=0`。

这属于实际 semantic coverage 增量，不是新的 wrapper、handoff 或状态面板。但它仍只是 local/offline software proof，因此只能把 O6/O7 保守上调到约 78%/78%，不归档任何 KR。

## OKR 映射和方向判断

- O6：继续。新增 DiagnosticArray decoded coverage 增强 archive/readback 对运行诊断材料的解释能力，但真实 production cloud、生产 DB/queue、真实机器人数据和现场长期回灌仍未证明。
- O7：继续但调整抓手。O7 能展示 DiagnosticArray decoded coverage，PC 复盘价值提升；下一步应优先拿真实/准现场 live Nav2 result、delivery record/operator confirmation 或 production cloud 证据，不应继续只补 decoder。
- KR 归档：本轮不归档 KR。证据仍是 local/offline fixture、unit test、O6 readback 和 O7 fixture/UI proof。

## 风险和阻塞

- 真实 route bag 未证明一定包含 `/diagnostics`，本轮 fixture 不能替代现场采集。
- `diagnostic_array_summary` 故意不输出 message/key/value 原文，能支持状态概览但不能替代原始故障日志。
- 当前链路不证明真实控制、真实路线执行、真实机器人运动或 delivery success，所有 action/control/submit 仍应保持 fail-closed。

## 验收结论

本轮按 PRD 验收通过，可以进入 final 收口。OKR 只做保守进度调整：O6/O7 约 76% -> 约 78%，无 KR 归档。
