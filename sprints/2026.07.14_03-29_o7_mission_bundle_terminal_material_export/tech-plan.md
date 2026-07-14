# Tech Plan：O7 Mission Bundle Terminal Material Export

## Owner

- `full-stack-software-engineer`

## 文件范围

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.14_03-29_o7_mission_bundle_terminal_material_export/tech-done.md`

范围外文件不得修改；若发现必须改范围外文件，先返回说明。

## 技术方案

- 在 `missionEvidenceBundleSectionSummaries` 的稳定 section 顺序里补入 `bounded_route_execution_gate_material` 与 `bounded_route_terminal_result_material`，位置应贴近 same-task replay / route material 类 section，便于 reviewer 按证据链阅读。
- 在 mission evidence bundle export 的 material section 分类集合中加入这两个 section，让 `material_section_count` 覆盖最新 O6/O7 bounded-route gate 与 O5 terminal-result material。
- 扩展 `catalog.test.ts` 的 mission evidence bundle export fixture，加入已有 helper 生成的 bounded route gate / terminal result material，并断言 section summary 与 material count。
- 文档同步说明 bundle export 会聚合这两个 material section，但仍固定 false fields，不证明真实路线执行、送达、HIL、production cloud 或 safe-to-control。

## 验收命令

```bash
cd pc-tools/workstation && npm run test -- test/catalog.test.ts -t "O7 mission evidence bundle export"
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
rg -n "bounded_route_terminal_result_material|bounded_route_execution_gate_material|material_section_count|software_proof_o7_o6_mission_evidence_bundle_export_only|route_execution_success=false|delivery_success=false|hil_pass=false" pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.14_03-29_o7_mission_bundle_terminal_material_export
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.14_03-29_o7_mission_bundle_terminal_material_export
```

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective 是 Objective 5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对原因：O5 当前缺真实公网 HTTPS/TLS success-class、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实 phone/browser 证据；最近 O5 CDN/TLS 仍 blocked 在 `blocked_http_status_not_success_class`，继续做本地 wrapper 不能带来 OKR lift。本轮转向 O7/O6 selected-task bundle export 的非重复合同缺口，消费上一轮已产生的 terminal material，但明确保持 OKR 百分比 flat。

## 风险与边界

- 该改动只修正 O7/O6 local/mock export 汇总一致性。
- 不得把 `bounded_route_terminal_result_material` 解读为 `route_execution_success=true`、`delivery_success=true` 或 `hil_pass=true`。
- 若全量 workstation 测试受既有未合入改动影响失败，需先定位是否与本轮文件有关；不能直接以首次失败收口。
