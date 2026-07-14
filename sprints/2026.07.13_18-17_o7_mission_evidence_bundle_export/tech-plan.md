# Tech Plan - O7 Mission Evidence Bundle Export

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective：Objective 5，约 `85%`。
2. 本 sprint 不直接推进 O5。
3. 原因：最近 O5 `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/` 已阻塞在 `blocked_http_status_not_success_class`。没有新的 success-class public endpoint、production DB/queue、worker cutover、OSS/CDN live traffic、4G/SIM 或真实 phone/browser 证据；继续 O5 会重复消费同一 blocker。O1/O3 current live route/HIL 也需要 explicit operator approval，本自动化不能代替授权。因此本轮转向不重复的 O7/O6 selected-task mission evidence bundle export。

## 技术方案

在 `pc-tools/workstation` 增加 O7 adapter：

- 新共享契约：`O7MissionEvidenceBundleExportResult`。
- 新 client helper：`getO7ConsumerMissionEvidenceBundleExport(baseUrl, taskId)`。
- 新 server route：`GET /api/o7/consumer-read/tasks/:taskId/mission-evidence/export`。
- 新 adapter function：`buildO7ConsumerMissionEvidenceBundleExport(baseUrl, taskId, format)`。
- Adapter 固定从本机回环 O6 `GET /api/o6/consumer/tasks/<task_id>?view=default&include=...` 读取 detail，不允许任意 endpoint。
- 复用现有安全 helper：loopback base URL、safe task id、dangerous true scan、safe path token/string list、false fields。
- 成功时只输出 local/mock summary：section counts、同一任务 identity、evidence refs basename、readiness/proof fields、blocked reasons、not_proven。
- UI 在 O7 consumer read primary path 中增加一个 export action 和 receipt 展示；没有 selected task/detail 时禁用或 fail closed。

## 文件范围

允许改：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.13_18-17_o7_mission_evidence_bundle_export/tech-done.md`

禁止改：

- 硬件/vendor 文件
- WAVE ROVER/UART 配置
- ROS2 launch 或实际控制路径
- O5 CDN/TLS probe
- 历史 sprint 文件

## 接口影响

新增 O7-only PC adapter endpoint：

`GET /api/o7/consumer-read/tasks/:taskId/mission-evidence/export?baseUrl=<local-loopback-url>&format=json`

该 endpoint 只返回 local/mock export receipt，不生产真实文件、不连接生产云、不开放真实下载。

## 验收命令

子 agent 必须运行并记录结果：

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
rg -n "mission evidence bundle|mission-evidence/export|o7_mission_evidence_bundle_export|software_proof_o7_o6_mission_evidence_bundle_export_only|safe_to_control=false|delivery_success=false|route_execution_success=false|hil_pass=false|不归档" pc-tools/workstation/src docs/interfaces docs/product sprints/2026.07.13_18-17_o7_mission_evidence_bundle_export/tech-done.md
git diff --check -- pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_18-17_o7_mission_evidence_bundle_export
```

## 风险边界

- 任何成功响应都必须固定 false safety/prod fields。
- 任何 remote detail dangerous true field 都必须 fail closed。
- Bundle export 只能消费 O6 consumer detail，不得绕过 O6 读取本地绝对路径或 raw artifact body。
- 本轮不更新 OKR 百分比，不归档 KR。
