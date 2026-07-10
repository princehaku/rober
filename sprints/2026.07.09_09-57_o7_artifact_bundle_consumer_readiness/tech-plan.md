# O7 Artifact Bundle Consumer Readiness Tech Plan

## 范围

本轮是 `full-stack-software-engineer` 单线闭环，主责把 O6 bundle 消费成 O7 readiness 摘要。允许改动文件仅限：

- `/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`
- `/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`
- `/Users/m1/apps/rober/docs/interfaces/o7_realtime_operator_console.md`
- `/Users/m1/apps/rober/pc-tools/README.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_09-57_o7_artifact_bundle_consumer_readiness/tech-done.md`

主节点不改产品代码和测试代码，只负责留档和收口判断。

## 技术方案

### O7 consumer readiness adapter

- 在 `o7ConsumerReadAdapter.ts` 中显式读取 O6 `artifact_bundle` / `artifact_bundle_consumer_ingest`。
- 将 bundle / preflight 中的 route、replay、keyframe、evidence、review item 信息统一归一为 `artifact_bundle_readiness` 摘要。
- 同一 `task_id` 下输出计数、样本 refs、blocked reasons、next required evidence。
- route replay / labeling 的阻塞原因和样本媒体 refs 优先来自 bundle / preflight，旧 fallback 只作为兼容兜底。

### Shared contract

- 在 `contracts.ts` 里补齐 readiness 相关类型，保证 UI 和 server 看到的是同一份结构化结果。
- 新字段只能 additive，旧 fixture 缺字段时继续 fail-closed 到 `derived_blocked_not_proven` 或同等安全状态。
- 所有危险字段继续保持 false，不允许把 sample ref、path、token、raw media、真实云地址误暴露成可执行能力。

### UI preview

- `O7FixturePreviewPanel.vue` 展示 readiness 摘要主路径，强调同一 `task_id` 下的计数、样本 refs、blocked reasons、next required evidence。
- 路由回放和标注相关信息直接显示“从 bundle 读到什么”，避免让旧 debug fixture 覆盖主路径。
- 任何真实媒体、真实云、真实送达或真实 annotation 的含义都必须保持不可推断。

### Tests and docs

- `catalog.test.ts` 和 `App.test.ts` 覆盖 readiness 摘要、fallback、dangerous false fail-closed 行为。
- `docs/product/pc_tools_workstation.md` 和 `docs/interfaces/o7_realtime_operator_console.md` 同步记录 O7 readiness 语义和边界。
- `pc-tools/README.md` 只做必要入口说明，不扩展为新的功能承诺。

## 接口影响

- 现有 O7 consumer detail 兼容旧 schema，但新增 `artifact_bundle_readiness` 为 additive 输出。
- 不新增 O6 写入接口，不改 O6 archive 行为。
- 旧 debug fixture 继续保留，但不能覆盖主路径，也不能把 blocked/not_proven 伪装成 ready。

## 验收命令

`full-stack-software-engineer` 必须运行：

```bash
cd pc-tools/workstation && npm run test -- --runInBand
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check
```

如果 vitest 不支持 `--runInBand`，则改为 `npm run test` 并在结果里记录原因。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节 active Objective 中最低完成度的是 O7，约 38%；其次是 O6，约 39%。本 sprint 直接针对 O7，并通过消费 O6 bundle 提升 O7 的 consumer readiness，符合最低优先级推进要求。

## 风险边界

- 本轮仅是 local/mock software proof。
- 不证明真实生产云、真实 OSS/CDN、真实媒体可访问、真实 annotation API、真实 dataset export、真实 RTC/视频、真实 ASR/TTS、真实机器人运动或 delivery success。
- 不引入新的硬件集成、不改底盘协议、不增加 O6 写入入口。
- 如果测试失败，必须先定位再修复后复验，不能把第一次失败当最终结果。
