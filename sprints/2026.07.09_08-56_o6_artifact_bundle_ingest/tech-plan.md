# O6 Artifact Bundle Ingest Tech Plan

## 目标

在 `remote_cloud_relay.py` 的 O6 local/mock archive 内新增或扩展 artifact bundle ingest 能力。输入是一份结构化、小型、安全摘要；输出是同一 file-backed store 中可回读的 task、trajectory、events、evidence refs、field/artifact 摘要和 media preflight 输入。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节最低 Objective 是 O6（约 37%），其次是 O7（约 38%）。本 sprint 直接针对 O6，不绕开最低 Objective。选择该项的原因是：最近两轮 O6/O7 没有被同一 blocker 阻塞，且当前环境虽然缺真实云/OSS/4G/媒体，但可以通过 local/mock artifact bundle ingest 继续推进 O6 KR2/KR3/KR6 的软件可验证结果。

## 文件范围

允许 Robot Software Engineer 修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.09_08-56_o6_artifact_bundle_ingest/tech-done.md`

不得修改 O7 前端、硬件配置、launch 参数、vendor 文档或无关 sprint。

## 接口方案

优先使用 additive 方案：

- 新增 `POST /api/o6/archive/artifact-bundle`，或在不破坏现有合同的前提下扩展 `POST /api/o6/archive/field-evidence` 接收 `artifact_bundle`。
- `artifact_bundle` 建议包含 `schema=trashbot.o6.artifact_bundle.v1`、`robot_id`、`task_id`、`route_refs[]`、`replay_refs[]`、`keyframe_refs[]`、`evidence_refs[]`、`trajectory_frames[]`、`events[]`。
- 所有 refs 只保存 basename 或安全相对 ref 摘要；禁止绝对路径、URL credential、token、base64/raw content、串口和控制 topic。
- 写入后 task/consumer detail 暴露 `artifact_bundle_ingest` 或等价摘要，且继续保留 `artifact_media_preflight` 的 local/mock/not_proven 边界。

## 风险和边界

- 本轮不证明真实文件存在或可读取。
- 本轮不证明真实 OSS/CDN、生产 DB/queue、真实 annotation API、真实 dataset export 或真实机器人控制。
- 如果实现发现已有 field-evidence ingest 已完整覆盖该合同，允许改为补齐测试和文档中缺失的 artifact bundle alias/readback，但必须留下新验证证据。

## 验收命令

Robot Software Engineer 必须运行并回报：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

```bash
git diff --check
```
