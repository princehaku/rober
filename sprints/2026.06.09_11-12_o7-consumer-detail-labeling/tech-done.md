# O7 Consumer Detail Labeling Queue Tech Done

## sprint_type

sprint_type: epic

## 1. 实际改动

本轮由 `full-stack-software-engineer` 单线完成，目标是把 O7 Previews 的标注能力从 archive fixture fallback 推进到 O6 consumer detail 主路径，并保持 submit/export/rollback 永久关闭。

收口时间：2026-06-09 11:17:54 CST。

- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 新增 `Consumer-detail labeling queue primary path` 视图，直接消费 `consumerTaskDetailResult` 中的 `labeling / evidence / events / trajectory` 摘要。
  - 增加 consumer-detail labeling 队列的 fail-closed 关闸逻辑：缺 detail、unknown task、task id mismatch、labeling/evidence/events/trajectory 缺失或任务状态不可审阅时，明确返回 blocked reason。
  - 新增只读 queue check rows，只输出短摘要，不透传 raw payload、绝对路径、token、串口或 `/cmd_vel`。
  - 显式展示 `submit_enabled=false`、`export_enabled=false`、`rollback_enabled=false`、`real_annotation_api_connected=false`、`dataset_export_available=false`，并把 `connects_cloud_production`、`safe_to_control`、`primary_actions_enabled`、`robot_control_executed` 保持为 false。
  - 保留旧 archive fixture labeling review panel 作为 debug fallback，并把文案改成“debug fallback / 与 consumer-detail labeling primary path 隔离”。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 O7 Previews 相关 fixture/断言，覆盖 consumer-detail labeling primary path 的展示文案、关闭字段和 fallback 隔离文案。
  - 新增 blocked 分支测试，验证当 consumer detail 的 labeling 样本为空时，主路径会以 `labeling_missing` 关闸，而不是误报成功。
- `pc-tools/README.md`
  - 记录 O7 consumer read primary path 现在同时服务历史回放和标注队列检查，并明确 submit/export/rollback 关闭。
  - 说明旧 archive fixture labeling review panel 仅保留为 debug fallback，和 consumer-detail 主路径隔离。
- `docs/product/pc_tools_workstation.md`
  - 更新 PC workstation 产品边界，说明 consumer-detail labeling primary path 已成为 O7 Previews 主路径的一部分。
  - 明确 archive fixture labeling review panel 只是 debug fallback，不能与主路径混淆。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 更新 O7 Previews 接口边界，写清 consumer-detail labeling primary path 的只读语义、关闭字段和缺失样本时的 fail-closed 行为。
  - 同步说明 archive fixture labeling review panel 仅作为 debug fallback，cursor/state 与 consumer-detail 主路径隔离。

## 2. 验证结果

以下命令已全部通过：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
git diff --check
```

关键日志：

- `npm run build`：`✓ 31 modules transformed.`，`✓ built in 929ms`
- `npm run test`：`Test Files  2 passed (2)`，`Tests  43 passed (43)`
- `npm run lint`：`eslint .` 无报错
- `git diff --check`：无输出，通过

## 3. 失败定位

本轮无验证失败。若后续回归失败，优先排查 TypeScript 模板类型、consumer-detail fixture 断言和 debug fallback 文案是否漂移，再重新运行四个验收命令。

## 4. 剩余风险

- 这轮仍是 software proof，没有证明真实 O6 annotation API、真实数据集导出、真实云归档或真实生产标注流水线已接通。
- 旧 archive fixture labeling review panel 仍保留为 debug fallback，未来如果要收缩 UI 面积，需要再开一轮清理。
- consumer-detail labeling primary path 只做只读检查，不新增 submit/export/rollback 真实动作。

## 5. 用户旅程变化

operator 现在可以先进入 O7 consumer read primary path，再在同一份 consumer detail 上完成标注队列检查；页面会明确显示当前只是只读检查视图，不会把 archive fixture fallback 误当成主路径。

## 6. 接口影响

未新增生产 API，也未修改 O6 consumer read contract。PC workstation 仅在 UI 层把 `labeling / evidence / events / trajectory` 摘要重组为 consumer-detail labeling primary path，并继续把 submit/export/rollback 锁死为 false。
