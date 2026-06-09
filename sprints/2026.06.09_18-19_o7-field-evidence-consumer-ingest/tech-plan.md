# Tech Plan - O7 Field Evidence Consumer Ingest

## 1. Sprint 类型

- `sprint_type: epic`
- 设计目标：把 `field_evidence_manifest` 接入 O7 PC 路线回放 / 标注消费链，保留 local/mock fallback，并把 live SSH 作为可选增强输入，而不是唯一成功路径。

## 2. 主责 owner

- `full-stack-software-engineer`

理由：这轮的核心落点在 `pc-tools/workstation` 的 O7 工作台、server adapter、shared contract 和 UI consumer path，不是底盘、硬件或 ROS2 主链路。

## 3. 是否需要并行

- **不需要并行。**

原因：这是一个共享 contract 驱动的单条消费链，最容易出问题的是 ingest contract、preview contract 和 UI contract 的一致性。单 owner 闭环比拆成多个 owner 更能减少返工。

如果后续发现 O6 archive 适配必须单独推进，也只能在同一 owner 主线里分阶段完成，不在本 sprint 里制造假并行。

## 4. 未来实施文件范围

### 主要代码范围

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/o7RouteReplayPreview.ts`
- `pc-tools/workstation/src/server/o7LabelingPreview.ts`
- `pc-tools/workstation/src/server/o7OperatorConsole.ts`
- `pc-tools/workstation/src/server/catalog.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7OperatorConsolePanel.vue`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/src/components/RouteDebugPanel.vue`
- `pc-tools/workstation/src/components/TrainingLabelingPanel.vue`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`

### 文档范围

- `pc-tools/README.md`
- `pc-tools/evidence/README.md`
- `docs/navigation/fixed_route_workflow.md`
- 必要时新增 `docs/navigation/o7_field_evidence_consumer_ingest.md`

## 5. 接口边界

### 输入

1. `field_evidence_manifest` JSON
2. 本地 route replay / labeling fixture JSON
3. 可选 live SSH 输出的只读摘要

### 输出

1. O7 route replay 的可视化数据结构
2. O7 labeling queue 的可视化数据结构
3. fail-closed 的 blocked reason 和 not_proven 标记
4. 可给后续 O6 archive 消费的任务 / 证据关联字段

### 必须保持关闭的能力

- 不发控制命令
- 不打开串口
- 不连接 ROS2
- 不把 preview 转成 success claim
- 不把 delivery_success 或 primary_actions_enabled 打开

## 6. 不允许写代码前必须满足的功能点完整性标准

在动手写代码之前，设计必须同时满足下面全部条件：

1. **入口完整**：明确一个主入口能从 manifest 进入 O7 消费链，而不是只有孤立 preview。
2. **fallback 完整**：local/mock 验收和 live SSH 验收共享同一输出结构。
3. **状态完整**：缺失材料、SSH 不可达、preflight 未 ready、fixture 不完整这四类状态都要有明确的 fail-closed 分支。
4. **契约完整**：shared contracts 里必须能表达 route replay / labeling 的关键字段，不允许 UI 自己猜。
5. **安全完整**：所有控制与成功声明保持 false，直到真实证据出现。
6. **可测完整**：至少有一组 local fixture 测试覆盖完整和缺失两种路径。
7. **可读完整**：文档能解释输入、输出、状态与边界，不让 reviewer 用猜的。

只要其中任一项缺失，就不能开始写实现代码。

## 7. 验收命令

未来工程实现后，必须运行并在 `tech-done.md` 贴出关键输出：

```bash
cd pc-tools/workstation && npm test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run api
curl -s "http://127.0.0.1:8787/api/o7/route-replay-preview?fixtureJson=pc-tools/evidence/fixtures/wave_rover_feedback_replay/pass/odom_once.jsonl"
curl -s "http://127.0.0.1:8787/api/o7/labeling-preview?fixtureJson=pc-tools/evidence/fixtures/wave_rover_hil_packet_intake/pass/operator_hil_report.json"
curl -s "http://127.0.0.1:8787/api/o7/operator-console"
curl -s "http://127.0.0.1:8787/api/o7/consumer-read/tasks?baseUrl=http://127.0.0.1:8088"
rg -n "field_evidence_manifest|route replay|labeling|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/workstation pc-tools/evidence docs/navigation
git diff --check
```

### 说明

- 本 sprint 的验收必须先证明 local/mock 路径可跑通。
- live SSH 路径如果当轮恢复，只能作为附加 smoke，不得成为唯一成功条件。
- 如果 live SSH 仍不可达，必须把不可达状态写进输出，但 local/mock 验收仍要完成。

## 8. OKR 最低优先级核对

当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 **O7：PC 端运营调试与数据训练平台（~12%）**。  
本 sprint **就是针对该最低 Objective**，原因是：

1. O7 的 route replay / labeling 正在缺少一个可运行的 evidence consumer。
2. 这一轮可以直接消化上一轮 field evidence manifest 的产出。
3. 只做 O3 现场 SSH 追逐会继续消费同一 blocker，不会抬升 O7 的可运行度。

## 9. 风险

1. live SSH 仍可能不可达，导致远端路径只能作为附加输入而非主验证手段。
2. route replay / labeling 的消费数据结构如果和现有 preview contract 不一致，可能需要补 shared contract。
3. 如果 UI / server 之间的状态语义不统一，容易把 blocked 误渲染成成功态。
4. O6 archive 如果被证明必须先补契约，可能会把本 sprint 的范围压缩回 O7 主线，不能临时扩成两个完整 Objective。

## 10. 下一步应派发的 Engineer

- 角色：`full-stack-software-engineer`
- 原因：O7 consumer ingest 的主风险在 workstation contract 和 UI 消费路径，不在硬件和 ROS2。

