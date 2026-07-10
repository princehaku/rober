# O6/O7 Route Bag Full Semantic Decode Matrix Tech Plan

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O6（约 71%）和 O7（约 71%）并列最低。
- 本 sprint 是否针对该最低 Objective：是。
- 选择理由：上一轮 final 明确仍缺 `raw ROS message payload 全量语义解析/回放`。本轮用现有 DB3 离线材料推进 per topic/type semantic decode coverage matrix，不依赖真实硬件/生产云，也不重复消费真实 4G、OSS、TLS 或 live route execution blocker。
- final.md 收口时需复核：是否确实新增 coverage matrix，而不是只新增 wrapper；是否保持 false safety fields；是否能作为 O6/O7 进度的保守提升依据。

## 三 Owner 并行任务分工

### 1. `robot-algorithm-engineer`

目标：在 `field_route_evidence_manifest.py` 中新增 `route_bag_full_semantic_decode_matrix`，输出 DB3 payload per topic/type 语义解码覆盖矩阵。

文件范围：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/algorithm_worker_report.md`

接口边界：

- schema：`trashbot.route_bag_full_semantic_decode_matrix.v1`
- proof_scope：`software_proof_route_bag_full_semantic_decode_matrix_only`
- 只读 SQLite DB3，继续使用 Python 标准库，不引入 ROS2 runtime。
- matrix item 只允许 safe topic/type、计数、状态、blocked reason、decoder name、安全 sample hash prefix；不得输出 raw payload、base64、完整 hash、绝对路径、token、URL credential、`/cmd_vel` 或成功控制字段。
- 顶层和 `field_motion_evidence_packet.route_bag_full_semantic_decode_matrix` 同步写入。

建议实现点：

1. 复用现有 `decode_semantic_message`、topic safety、DB3 schema 检查和 source label sanitizer。
2. 对每个 topic/type 聚合 limited sample decode，支持类型计入 decoded，未知安全类型计入 unsupported，异常计入 failed。
3. `status` 仅在 DB3 可读、至少有 decoded type、无 unsafe/dangerous true 时为 `ready_not_route_execution_proof`；否则 `blocked_not_proven`。
4. `coverage_ratio` 用 decoded message samples / considered message samples，保留 3 位小数。
5. 测试覆盖 ready matrix、unsupported type、corrupt payload、missing DB3、unsafe topic。

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

### 2. `robot-software-engineer`

目标：把 Algorithm 的 matrix 接入 O6 archive/readback/consumer include。

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/o6_worker_report.md`

接口边界：

- 输入 schema：`trashbot.route_bag_full_semantic_decode_matrix.v1`
- O6 输出 schema：`trashbot.o6.route_bag_full_semantic_decode_matrix.v1`
- proof_scope 必须匹配 `software_proof_route_bag_full_semantic_decode_matrix_only`。
- 支持 field evidence、artifact bundle、archive task detail、consumer detail 和 `include=route_bag_full_semantic_decode_matrix`。
- 继续 fail-closed：坏 schema、坏 proof scope、危险 true、unsafe topic/text/path/url/token/raw/base64、缺必填计数或负数都返回 blocked summary。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

### 3. `full-stack-software-engineer`

目标：O7 消费 O6 matrix，并在 artifact bundle readiness 与 UI 中只读展示。

文件范围：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/o7_worker_report.md`

接口边界：

- O7 只能消费 O6 或 Algorithm 已定义的 matrix summary，不自行发明成功语义。
- UI 显示 decoded/unsupported/failed counts、coverage ratio、sample topic/type、blocked reasons、next evidence 和 false safety fields。
- `ready` 只表示本地/离线 semantic coverage 可读，不表示 route execution success 或 delivery success。
- 坏 schema、危险 true、unsafe 文本或控制 topic 必须 fail-closed。

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

## 主责与集成验收

- 主责 owner：`robot-software-engineer`
- 原因：本轮核心是 Algorithm matrix 被 O6 安全接入后供 O7 消费，O6 是跨 lane 的合同收束点。
- Product/main 只做证据核对、sprint 文档收口和 OKR 保守更新判断。

## 产品收口文件范围

Product/main 后续收口可改：

- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/tech-done.md`
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/side2side_check.md`
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

说明：三个 implementation worker 的写范围互不重叠，避免并行写同一个 `tech-done.md`。主会话在三方 worker report 返回后统一写 `tech-done.md`、`side2side_check.md` 和 `final.md`。

## 风险边界

- 本轮只做 local/offline software proof。
- 不证明真实 production cloud、真实 DB/queue、真实 OSS/CDN、真实 4G/TLS。
- 不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 不把 unsupported/failed decode 隐藏；它们必须作为可见缺口进入 matrix。
