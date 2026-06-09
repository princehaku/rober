# O7 Offline Manifest Consumer Detail Tech Plan

## sprint_type: micro

## 责任 Engineer

- 主责 owner：`full-stack-software-engineer`
- 本轮单 owner 闭环，不并行拆分，避免 PC adapter/UI/test 共享文件冲突。

## 设计

在 O7 consumer detail 主路径上增加可选本地 manifest 输入：

```text
GET /api/o7/consumer-read/tasks/:taskId?baseUrl=<loopback>&fieldEvidenceManifestJson=<local-json>
```

语义：

- `baseUrl` 仍只允许本机 loopback HTTP relay。
- `fieldEvidenceManifestJson` 只由 PC 后端读取本地 JSON，浏览器不直连文件。
- 若远端 O6 detail 已提供有效 `field_evidence_manifest` 或 `field_evidence_consumer_ingest`，优先使用远端合同。
- 若远端 O6 detail 缺失 field evidence，且本地 manifest 合法，则用本地 manifest 补齐 `field_evidence`。
- 若本地 manifest 缺失、坏 JSON、schema mismatch、非 object root、包含危险 true claim 或 unsafe copy，则 detail 必须 fail-closed。
- 该输入只影响只读 evidence 摘要，不改变 trajectory/events/evidence/labeling/inference/tunnel 的来源。

## 文件范围

允许改动：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.06.09_22-02_o7-offline-manifest-consumer-detail/tech-done.md`

不得改动：

- `onboard/**`
- `cloud-relay/**`
- 硬件/vendor 资料
- 其他 sprint 目录

## 验收命令

子 agent 必须执行并上报：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
rg -n "fieldEvidenceManifestJson|trashbot.field_evidence_manifest.v1|safe_to_control=false|primary_actions_enabled=false|delivery_success=false" pc-tools docs/product/pc_tools_workstation.md sprints/2026.06.09_22-02_o7-offline-manifest-consumer-detail
git diff --check
```

## 风险

- 这是 `software_proof_local_manifest_consumer_detail_only`，不是真实云 archive、真实 O6 生产链路、真实路线回放、真实标注提交或真实机器人运动。
- 如果 O6 detail 本身出现危险 true 字段，仍必须整体 fail-closed，本地 manifest 不得绕过远端危险声明。
- 如果 UI 文案不足，operator 可能把 artifact gate 误读为送达成功；因此页面和文档必须显式显示 false 控制字段。
