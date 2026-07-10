# O6 Artifact Access Probe Side2side Check

- sprint_type: epic
- check_time: 2026-07-09 11:55 CST
- product_owner: product-okr-owner
- target_objective: O6 云端核心后端
- secondary_objective: O7 PC 端运营调试与数据训练平台
- evidence_boundary: software_proof_local_mock_artifact_access_probe_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 用户价值和产品北极星

本轮把 O6/O7 从“看见 artifact ref 或 readiness 摘要”推进到“能在受限 allowlist root 内证明本地/mock 小文件可读，并把 exists、size、sha256、detected_type 和 blocked_reason 回读给 PC consumer”。这减少了后续路线回放、标注和训练数据链路把空字符串、危险路径或不可访问文件误当成可用证据的风险。

产品北极星不变：让普通用户把垃圾交给小车后，小车可验证地完成垃圾投递。本轮只补可复盘数据底座，不证明真实机器人运动、真实投递、真实媒体访问或生产云可用。

## 计划对照

| PRD/Tech Plan 要求 | 实际结果 | 验收判断 |
| --- | --- | --- |
| O6 新增 `artifact_access_probe`，对 artifact bundle / field evidence refs 生成只读摘要 | 已实现 `trashbot.o6.artifact_access_probe.v1`，支持 `artifact_access_root` / `TRASHBOT_O6_ARTIFACT_ACCESS_ROOT`、64KB 上限、exists/size/sha256/detected_type/blocked_reason/proof_scope | 通过 |
| 只允许读取 allowlist root 内安全相对小文件 | O6 对 root 缺失、root 无效、绝对路径、`..`、URL/query、credential/control/raw/base64、越界、目录、缺文件和超 64KB fail-closed | 通过 |
| archive task detail、field_evidence、artifact_bundle、consumer detail 和 include 回读 probe | O6 已暴露到 archive detail、field_evidence、artifact_bundle、consumer detail 与 `include=artifact_access_probe` | 通过 |
| O7 只能 secondary 消费 O6 probe，不新增独立事实来源 | O7 读取 top-level / nested `artifact_access_probe`，在 readiness/UI 展示 counts、basename refs、detected_type、size、sha256 prefix、blocked reasons、next evidence | 通过 |
| 所有危险能力字段保持 false | `safe_to_control: false`、`delivery_success: false`、`primary_actions_enabled: false`、`robot_control_executed: false` 均保持 false | 通过 |

## 验证证据

Robot/O6 worker 证据：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
通过，无输出
```

```text
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
首次失败后修复 blocked reason 判定顺序
Ran 153 tests in 52.427s
OK
```

```text
git diff --check
通过，无输出
```

Full-stack/O7 worker 证据：

```text
cd pc-tools/workstation && npm run test
Test Files  3 passed (3)
Tests       472 passed (472)
```

```text
cd pc-tools/workstation && npm run build
首次 TypeScript TS2783 重复字段失败后修复
复验通过，Vite 仅既有 large chunk warning
```

```text
cd pc-tools/workstation && npm run lint
通过，无 ESLint 输出
```

```text
git diff --check
通过，无输出
```

## OKR 映射和方向判断

方向判断：继续 O6/O7，不暂停、不替换，不归档 KR。

- O6 KR2/KR3/KR6 推进：archive/read model 已能围绕同一 `task_id` 保存并回读 artifact 可访问性摘要，但仍只是 file-backed local/mock proof。
- O7 KR3/KR4 推进：PC/O7 consumer detail 已能展示 artifact access probe readiness、blocked reasons 和 next evidence，但仍不是生产回放或真实标注完成态。
- 本轮证据支持 O6 从约 39% 保守上调到约 42%，O7 从约 40% 保守上调到约 42%。
- 已完成 KR 历史归档：无。没有任何 KR 被标为完成或移入历史区。

## 证据边界和剩余缺口

本轮唯一证据边界是 `software_proof_local_mock_artifact_access_probe_only`。

不证明：

- 真实 OSS/CDN、production cloud、生产 DB/queue、TLS/4G 或公网隧道。
- 真实机器人数据、真实媒体访问、真实 keyframe 可打开、真实 route replay 可播放。
- 真实 annotation API、真实 dataset export、真实 RTC/视频、真实 ASR/TTS。
- ROS2 runtime、机器人运动、wheel raw 非零、完整路线长期验收或 delivery success。

下一步验收应直接要求真实或离线 artifact seed：至少把一个现场 `route.csv`、replay JSONL、keyframe 或 rosbag 放入 allowlist root，证明 O6/O7 对同一 `task_id` 可消费真实/离线文件摘要，而不是继续叠加 local/mock wrapper。
