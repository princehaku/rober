# Side-by-side Check - O7 Mission Evidence Bundle Export

## 对照结论

Product 接受本轮为 O7/O6 selected-task local/mock mission evidence bundle export software proof only。

接受边界：

- Proof boundary：`software_proof_o7_o6_mission_evidence_bundle_export_only`
- 新 endpoint：`GET /api/o7/consumer-read/tasks/:taskId/mission-evidence/export?baseUrl=<local-loopback-url>&format=json`
- 新 receipt schema：`trashbot.pc_tools_workstation.o7_mission_evidence_bundle_export_result.v1`
- 成功状态：`local_mock_mission_evidence_bundle_ready`
- UI 只在 selected task detail 已加载且匹配时允许导出；未加载、fail-closed 或 task mismatch 时不伪造成功。

拒绝边界：

- 不是 production cloud、real cloud DB、real OSS、production DB/queue、OSS/CDN、4G/SIM 或真实 phone/browser proof。
- 不是 route execution、delivery/operator acceptance、delivery success、HIL、safe-to-control 或 O5 external evidence。
- 不触碰 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、硬件/vendor 文件或 ROS2 launch。

## 验证证据

Full-stack worker 已运行并记录：

- `cd pc-tools/workstation && npm run test`：通过，`Test Files 3 passed (3)`、`Tests 504 passed (504)`。
- `cd pc-tools/workstation && npm run build`：首轮因 App test fixture 重复 false fields 失败，修复后通过；只保留既有 Vite large chunk warning。
- `cd pc-tools/workstation && npm run lint`：通过。
- proof-boundary `rg`：通过，命中 endpoint、schema、proof scope、UI copy、docs 和 `tech-done.md`。
- scoped `git diff --check`：通过。

## OKR 判定

- O5 继续约 `85%`：本轮没有 success-class public endpoint、production DB/queue、worker cutover、OSS/CDN live traffic、4G/SIM 或真实 phone/browser evidence。
- O1 继续约 `94%`：本轮没有 current live HIL、safe-to-control、Nav2 route execution success 或现场 delivery/operator acceptance。
- O6/O7 继续约 `93%`：本轮是 selected-task bundle export receipt，比 query/readback wrapper 更强，但仍是 local/mock software proof。
- 本轮 KR `不归档`，主百分比不调整。

## 剩余风险

- Bundle receipt 只聚合 O6 consumer detail 的白名单摘要，不生成真实文件、不写生产云、不读取 raw artifact body。
- 若后续把该 receipt 当作真实路线执行、真实送达、HIL 或生产云成功，需要按 OKR 边界返工。
- 下一轮优先 explicit operator-approved current live HIL/current route evidence，或真实 production/cloud evidence；若仍不可得，O7/O6 只能继续接更强 same-task mission artifact，不重复 delivery-result/write wrapper。
