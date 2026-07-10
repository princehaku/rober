# O6 Artifact Access Probe Tech Plan

## 目标

在 O6 archive/read model 中新增 artifact access probe 摘要能力。输入来自现有 artifact bundle 或 field evidence 的本地/mock refs；输出是在同一 `task_id` 下可回读的安全摘要，包括存在性、大小、sha256、类型和 blocked reason。

本轮不实现生产云访问，不读取 token URL，不执行机器人控制。所有行为默认 fail-closed。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节 active Objective 中最低完成度是 O6，约 39%；其次是 O7，约 40%。本 sprint 直接针对最低 Objective O6，不绕开最低优先级。

选择 O6 的理由：

- 最近 O6/O7 多轮 final 已明确指出，不能继续只堆 local/mock wrapper、summary 或 readiness surface。
- O6 已有 `field_evidence`、`artifact_media_preflight`、`artifact_bundle` 和 consumer detail 回读基础，具备推进 artifact access probe 的软件前提。
- 当前缺真实生产云、OSS/CDN、TLS/4G 和真实机器人长期数据，但可以先用受限本地/mock fixture 证明 artifact ref 可访问性摘要，直接推进 O6 KR2/KR3/KR6。

## Owner 分工

### `robot-software-engineer`

主责单线闭环 O6：

- 设计并实现 `artifact_access_probe` 数据结构和 readback 逻辑。
- 将 probe 接入 artifact bundle / field evidence 的本地 refs。
- 建立 allowlist root、相对路径规范化、大小上限、sha256、类型识别和 blocked reason。
- 补 O6 单元测试、接口文档和 `tech-done.md`。

### `full-stack-software-engineer`

次责，只在 O6 probe 合同稳定后介入：

- 读取 O6 consumer detail 的 `artifact_access_probe`。
- 在 O7 consumer/readiness 视图中展示 probe summary、blocked reasons 和 next required evidence。
- 保持所有 `local_mock/not_proven` 边界，不新增独立 wrapper。

### `robot-algorithm-engineer`

只读或事实补充：

- 如工程同学需要，提供 route.csv、replay JSONL、keyframe、rosbag 或 field evidence seed 的最小字段事实。
- 本轮不要求采集新地图、运行 Nav2、启动 ROS2 runtime 或生成真实路线。

## 文件范围

允许 `robot-software-engineer` 修改：

- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- `/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_10-58_o6_artifact_access_probe/tech-done.md`

允许 `full-stack-software-engineer` 在 O6 合同稳定后修改：

- `/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`
- `/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`
- `/Users/m1/apps/rober/docs/interfaces/o7_realtime_operator_console.md`
- `/Users/m1/apps/rober/pc-tools/README.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_10-58_o6_artifact_access_probe/tech-done.md`

不得修改：

- `OKR.md`
- 硬件配置、launch 参数、vendor 文档
- 与 O6/O7 artifact access probe 无关的 sprint 目录
- 机器人控制路径、串口协议、底盘参数或 ROS2 motion runtime

## 接口影响

O6 additive 输出建议：

- 在 archive task detail 和 consumer detail 中新增 `artifact_access_probe`。
- `artifact_access_probe.schema` 建议为 `trashbot.o6.artifact_access_probe.v1`。
- `artifact_access_probe.task_id`、`robot_id` 与 archive task 保持一致。
- `artifact_access_probe.probes[]` 每项建议包含：
  - `ref`
  - `source`
  - `exists`
  - `size_bytes`
  - `sha256`
  - `detected_type`
  - `blocked_reason`
  - `proof_scope`

输入来源：

- `artifact_bundle.route_refs[]`
- `artifact_bundle.replay_refs[]`
- `artifact_bundle.keyframe_refs[]`
- `artifact_bundle.evidence_refs[]`
- `field_evidence` 或 `field_evidence_manifest` 中的本地相对 refs

安全规则：

- 仅允许读取配置或测试 fixture 指定的本地 allowlist root 内文件。
- refs 必须是相对路径或安全 basename；绝对路径、`..`、URL、token query、credential hint、raw/base64 content、串口设备路径和 ROS topic 一律 blocked。
- 默认文件大小上限必须保守；超过上限只返回 blocked reason，不读取完整内容。
- hash 只对允许且大小合规的文件计算。
- 不将本机绝对路径、token、原始媒体内容或文件全文写入 archive。

O7 additive 输出建议：

- O7 consumer detail 可读取 `artifact_access_probe` 并派生 readiness。
- O7 只能展示 counts、sample refs、sha256 前缀、blocked reasons 和 next required evidence。
- O7 不得因为 `exists=true` 就声明真实媒体可播放、真实回放完成或 production ready。

## 实现顺序

1. `robot-software-engineer` 先实现 O6 probe 数据结构、路径安全校验和 readback。
2. 增加最小 fixture：一个安全小文件，一个缺失或 blocked ref。
3. 补 O6 测试：happy path、missing file、unsafe ref、consumer detail readback、dangerous true fail-closed。
4. 更新 O6 文档，写清 `software_proof_local_mock_artifact_access_probe_only`。
5. 如果 O6 合同稳定且时间允许，再由 `full-stack-software-engineer` 做 O7 secondary consumer 展示和测试。
6. 实现阶段必须更新 `tech-done.md`；收口阶段再补 `side2side_check.md` 和 `final.md`。

## 验收命令

`robot-software-engineer` 必须运行并回报：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

如 `full-stack-software-engineer` 参与 O7 secondary consumer，必须运行并回报：

```bash
cd pc-tools/workstation && npm run test
```

```bash
cd pc-tools/workstation && npm run build
```

```bash
cd pc-tools/workstation && npm run lint
```

所有参与者最终必须运行：

```bash
git diff --check
```

Product 计划阶段轻量验收命令：

```bash
test -f sprints/2026.07.09_10-58_o6_artifact_access_probe/pre_start.md && test -f sprints/2026.07.09_10-58_o6_artifact_access_probe/prd.md && test -f sprints/2026.07.09_10-58_o6_artifact_access_probe/tech-plan.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O6|artifact access probe|robot-software-engineer|full-stack-software-engineer|验收命令" sprints/2026.07.09_10-58_o6_artifact_access_probe
```

## 风险边界

- 本轮证据边界是 `software_proof_local_mock_artifact_access_probe_only`。
- 不证明真实 production DB/queue、OSS/CDN、TLS/4G、公网隧道、真实 annotation API、真实 dataset export 或生产级查询容量。
- 不证明真实媒体可播放、真实 keyframe 可打开、真实路线回放完成、真实 RTC/视频、真实 ASR/TTS、wheel raw 非零或 delivery success。
- 不允许读取 token URL、credential URL、绝对路径、父目录逃逸路径、raw/base64 内容、串口设备或 ROS topic。
- 不启动 ROS2 runtime，不连接机器人，不下发 `/cmd_vel`，不执行任何底盘或任务控制。
- 如果没有真实或离线 artifact seed，本轮可以用 fixture-only 验证，但 `tech-done.md` 和 `final.md` 必须明确剩余风险：仍需补真实/离线 route.csv、replay JSONL、keyframe 或 rosbag smoke。
