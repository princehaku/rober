# O6/O7 Route Execution Result Delivery Readiness Tech Plan

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O6（约 68%）和 O7（约 68%）并列最低。
- 本 sprint 是否针对该最低 Objective：是。
- 选择理由：上一轮 `route_bag_pose_progress_replay` 已明确下一步优先缺口是 live Nav2 route execution result、delivery record / operator confirmation 和 production cloud。本轮直接命中其中“结果链路 readiness”这条最可推进的软件工作，避免继续堆纯只读 wrapper。
- final.md 收口时需复核：是否仍然只是 software proof；是否围绕同一 `task_id` 实际打通 route execution result 与 delivery/operator confirmation readiness；是否有足够依据保守更新 O6/O7 进度且仍不归档 KR。

## 用户价值和北极星

这轮不是再造一层 summary，而是把“路线执行结果、投递 readiness、操作员确认 readiness”收束到同一 `task_id`，让运营和后续手机端知道任务结果证据已经到哪一步、下一步还缺什么。北极星仍是“普通用户可验证地完成垃圾投递”，但本轮边界严格限定为 software proof 的结果链路接线。

## 方向判断

- 继续推进 O6/O7。
- 不调整到 O1/O5，因为当前最低 active Objective 仍是 O6/O7，且本轮存在明确、可执行、非 blocker 重复消费的软件工作。
- 不暂停，因为 route execution result / delivery readiness 是上一轮 final 明确指向的下一跳。
- 不替换为 production cloud，本轮先完成本地/fixture/mock 的结果链摘要，再为 production cloud 提供清晰输入合同。

## 三 Owner 并行任务分工

### 1. `robot-algorithm-engineer`

目标：在 Algorithm manifest / field packet 中产出同一 `task_id` 的 `route_execution_result_delivery_readiness` 安全摘要。

文件范围：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/artifacts/algorithm_worker_report.md`

接口边界：

- 输入可以来自已有 fixture/mock/离线路线材料。
- 只能输出 summary-only 合同：状态、短标签、计数、basename refs、sha256 prefix、blocked reasons、next evidence、false safety fields。
- 不输出绝对路径、完整 payload、完整 hash、token、URL credential、控制结果或真实送达完成暗示。
- 需要把 route execution result 与 delivery/operator confirmation readiness 挂到 manifest 顶层和 field packet，供 O6 统一消费。

建议实现点：

1. 新增或扩展 route execution result / delivery readiness / operator confirmation readiness schema 常量与 proof scope 常量。
2. 对 route execution result 只保留安全摘要，如 source/status/result readiness/blockers。
3. 对 delivery/operator confirmation 只保留 readiness，不写真实完成断言。
4. 缺失输入、unsafe 文本、危险 true、字段冲突时 fail-closed 到 `blocked_not_proven`。
5. 补测试覆盖 ready、missing、unsafe、conflicting、nested packet。

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

### 2. `robot-software-engineer`

目标：把 Algorithm 的 route execution result / delivery readiness / operator confirmation readiness 接入 O6 archive ingest、detail readback、consumer detail 和 `include=`。

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/artifacts/o6_worker_report.md`

接口边界：

- 只接受 Algorithm 定义的安全摘要，不反向扩展 schema。
- 只在 O6 内做 additive ingest/readback，不改控制链路，不引入 live Nav2、真实云端或真实 delivery success 断言。
- 必须在 field evidence、artifact bundle、archive detail、consumer detail 和 `include=` 上保持一致合同。
- 坏 schema、危险字段、unsafe 文本、缺失必填项时降级为 `blocked_not_proven`。

建议实现点：

1. 新增 O6 对应 schema / proof scope / sanitizer。
2. 支持 route execution result / delivery/operator confirmation readiness 的 archive 读写归一化。
3. 保持 `safe_to_control=false`、`delivery_success=false`。
4. 补测试覆盖正常 ingest/readback、include 独立读取、unsafe fail-closed。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

### 3. `full-stack-software-engineer`

目标：在 O7 consumer detail / UI 中读取并展示 route execution result 与 delivery/operator confirmation readiness。

文件范围：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/artifacts/o7_worker_report.md`

接口边界：

- 只能消费 O6 已定义的结果链摘要，不自行发明另一个结果口径。
- UI 只读展示结果状态、blocked reasons、next evidence、样本 refs、false safety fields。
- 不解锁 submit/control/play/dispatch/发车动作，不制造“已完成 delivery”的视觉误导。
- 坏 schema、危险 true、unsafe 文本时必须 fail-closed。

建议实现点：

1. shared contract 增加 route execution result / delivery readiness / operator confirmation readiness summary。
2. adapter 从 O6 detail 合法位置归一读取并合并 blocked reasons / next evidence。
3. UI 增加只读结果摘要区块，延续现有 additive readiness 风格。
4. 测试覆盖 consumer read、artifact bundle readiness 汇总、UI DOM、unsafe fail-closed。

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

## 主责与集成验收

- 主责 owner：`robot-software-engineer`
- 原因：本轮核心是 Algorithm 合同进入 O6 archive/readback，再被 O7 消费；O6 是三方之间的主链路集成点。
- Product 只在三方 worker 返回后做证据核对、风险判断和 sprint 收口。

## 产品收口文件范围

Product 后续收口可改：

- `sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/tech-done.md`
- `sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/side2side_check.md`
- `sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/final.md`

当前任务不改 `OKR.md`、不改 `docs/process/`。

## 验收命令

Algorithm:

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

O6:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

O7:

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

Final/docs:

```bash
git diff --check -- sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/pre_start.md sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/prd.md sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/tech-plan.md
```

## 风险边界

- 本轮只做 software proof，不证明真实 production cloud、真实 4G/TLS、production DB/queue、真实 OSS/CDN。
- 不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success。
- 结果链的任何 `ready` 都只能表示“该摘要在本地/fixture/mock 证据下可读回”，不能表示“现场已完成”。
- 若任一 owner 只能新增 wrapper 而不能产出同一 `task_id` 的结果摘要，应停止扩 scope，并在 worker report 中写明原因。

## 需要做什么

1. 按上述三 owner 文件范围并行派单。
2. 要求每个 owner 在 worker report 中返回改动文件、验收输出、失败定位、剩余风险。
3. 三方完成后由 Product 验收是否满足“同一 `task_id` 结果链可读回”这一 P0 目标，再决定 O6/O7 是否保守上调。
