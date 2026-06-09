# O7 Consumer Detail Labeling Queue Final

## 1. 收口状态

状态：completed。

本轮已完成 O7 KR4 的 consumer-detail labeling queue 主路径：operator 在 O7 Previews 中加载 O6 consumer task detail 后，可以基于同一份 `labeling/evidence/events/trajectory` 摘要进行只读标注队列检查。旧 archive fixture labeling review panel 保留为 debug fallback，并与 consumer-detail 主路径隔离。

收口时间：2026-06-09 11:19:04 CST。

## 2. 实际改动

- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`：新增 `Consumer-detail labeling queue primary path`、blocked reason、只读 queue rows 和关闭字段展示；旧 labeling panel 改为 debug fallback 文案。
- `pc-tools/workstation/test/App.test.ts`：补充 consumer-detail labeling 主路径断言和 `labeling_missing` fail-closed 分支测试。
- `pc-tools/README.md`：记录 consumer read primary path 现在同时服务 route replay 和 labeling queue 检查。
- `docs/product/pc_tools_workstation.md`：同步 PC workstation 产品边界。
- `docs/interfaces/o7_realtime_operator_console.md`：同步 O7 Previews 接口边界。
- `sprints/2026.06.09_11-12_o7-consumer-detail-labeling/`：补齐 epic sprint 设计、实现、对照检查和收口记录。

## 3. 验证结果

工程验证全部通过：

- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm run test`：通过，`2 passed (2)` / `43 passed (43)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过。

## 4. OKR 回顾

本轮直接推进 O7 KR4 数据标注/打标界面，并复用 O6 consumer read detail 作为主输入。

`OKR.md` 4.1 中最低 Objective 仍是 O6。`tech-plan.md` 中“不直接针对 O6”的理由仍成立：上一轮已经把 O6 consumer read 读模型变成 O7 route replay 主路径，本轮继续把同一份 consumer detail 转化为 O7 labeling queue 用户价值，避免在同一层重复造读模型。

## 5. 剩余风险

- 仍是 software proof，不证明真实 O6 annotation API、真实数据集导出、真实云归档、真实生产标注流水线或真实上车数据。
- submit/export/rollback 仍固定关闭；真实写入能力需要单独设计、权限、审计和验收。
- 旧 archive fixture labeling review panel 仍保留为 debug fallback，后续如产品决定收缩 fallback 面积，需要另开 sprint。

## 6. 下一步建议

下一轮建议二选一：

- 回到 O6 最低 Objective，推进真实/准真实 consumer read deployment probe 或 annotation API mock-to-contract 闭环。
- 继续 O7 consumer detail 主路径，推进 voice ASR/TTS 或 safe command 的只读审计视图，但仍保持真实动作关闭。
