# O6/O7 Route Bag Odometry Semantic Decoder Tech Plan

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O6（约 74%）和 O7（约 74%）并列最低。
- 本 sprint 是否针对该最低 Objective：是。
- 选择理由：上一轮 final 明确要求继续补更多安全 ROS message decoder，让 matrix 把 unsupported 类型逐步转成 decoded evidence。本轮选择已有 pose progress 安全解析基础的 `nav_msgs/msg/Odometry`，避免重复消费真实 production cloud / live Nav2 / delivery success blocker。
- final.md 收口时需复核：是否确实新增 Odometry decoded 覆盖，而不是只新增 wrapper；是否保持 false safety fields；是否把证据边界写清楚。

## 三 Owner 并行任务分工

### 1. `robot-algorithm-engineer`

目标：复用现有 Odometry 位姿 CDR 解析，把 `nav_msgs/msg/Odometry` 纳入 `route_bag_semantic_replay` 与 `route_bag_full_semantic_decode_matrix` 的安全 semantic decoder。

文件范围：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/artifacts/algorithm_worker_report.md`

接口边界：

- 不新增 schema；沿用 `trashbot.route_bag_semantic_replay.v1` 与 `trashbot.route_bag_full_semantic_decode_matrix.v1`。
- decoder label 建议为 `odometry` / `decode_odometry_payload`。
- 摘要只允许 frame pair、position sample count、start/end translation、nonzero displacement observed 等安全字段；不输出 covariance、twist、raw payload、base64、完整 hash、绝对路径、token、URL credential 或控制 topic。
- Odometry corrupt payload 必须进入 failed；unsafe frame id 必须 fail-closed。

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

### 2. `robot-software-engineer`

目标：确认 O6 对 Odometry matrix item 和 semantic replay topic type 的归一、回读与 fail-closed 语义稳定。

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/artifacts/o6_worker_report.md`

接口边界：

- O6 只接收 Algorithm 产出的安全 summary，不自行解析 raw ROS payload。
- `topic_type_matrix[]` 可出现 `nav_msgs.msg.Odometry` 或等价安全规范化 type，状态为 `decoded`，decoder label 为 `decode_odometry_payload`。
- 继续校验 counts、coverage ratio、blocked reasons、next required evidence 和所有 false safety fields。
- 坏 schema、坏 proof_scope、危险 true、unsafe topic/text/path/url/token/raw/base64、负数计数仍返回 `blocked_not_proven`。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

### 3. `full-stack-software-engineer`

目标：O7 consumer 与 UI 展示 Odometry decoded matrix item，并保持只读、安全、非成功证明口径。

文件范围：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/artifacts/o7_worker_report.md`

接口边界：

- O7 只能显示 O6/Algorithm 已提供的 matrix/semantic summary，不发明 route execution success。
- UI 显示 Odometry decoded type、decoder label、counts、coverage ratio、blocked reasons、next evidence 和 false safety fields。
- `ready_not_route_execution_proof` 只表示本地/离线语义覆盖可读，不表示真实 route execution 或 delivery success。

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

## 主责与集成验收

- 主责 owner：`robot-algorithm-engineer`
- 原因：本轮核心增量是安全 ROS message decoder 覆盖扩展，O6/O7 只做消费与显示验证。
- Product/main 只做证据核对、sprint 文档收口和 OKR 保守更新判断。

## 产品收口文件范围

Product/main 后续收口可改：

- `sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/tech-done.md`
- `sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/side2side_check.md`
- `sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

说明：三个 implementation worker 的写范围互不重叠，避免并行写同一个 `tech-done.md`。主会话在三方 worker report 返回后统一写 `tech-done.md`、`side2side_check.md` 和 `final.md`。

## 风险边界

- 本轮只做 local/offline software proof。
- 不证明真实 production cloud、真实 DB/queue、真实 OSS/CDN、真实 4G/TLS。
- 不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 不把 Odometry decoded coverage 外推成完整 raw ROS message payload 全量语义回放。
