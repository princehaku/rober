# O6 Artifact Bundle Ingest Tech Done

## Sprint 类型

- sprint_type: epic
- implementation_owner: robot-software-engineer
- target_objective: O6
- evidence_boundary: software_proof_local_mock_artifact_bundle_ingest_only

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `POST /api/o6/archive/artifact-bundle` local/mock ingest 入口。
  - 复用现有 file-backed O6 archive store，把 `trashbot.o6.artifact_bundle.v1` 结构化摘要转换为同一 `task_id` 下的 task、trajectory、events、evidence refs 和 `artifact_media_preflight`。
  - 为 archive task detail / consumer detail 新增 `artifact_bundle`、`artifact_bundle_consumer_ingest` 回读 alias，并保持所有危险字段为 `false`。
  - 让 `POST /api/o6/archive/field-evidence` 在收到 `artifact_bundle` wrapper 或直传 `trashbot.o6.artifact_bundle.v1` 时走同一条 ingest 逻辑，保持 additive 兼容。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 新增 artifact bundle happy path、archive detail / consumer detail 回读、`field-evidence` 兼容 alias，以及 empty refs / dangerous true / unsafe ref fail-closed 测试。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 补充 `POST /api/o6/archive/artifact-bundle` 合同、`field-evidence` 兼容 alias 说明，以及 archive/consumer readback 的 additive alias 说明。

## 验证结果

执行命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

结果：通过。

```text
................................................................................
Ran 151 tests in 50.374s

OK
```

```bash
git diff --check
```

结果：通过，无输出。

## 失败定位

- 本轮验证中未出现需要二次修复的失败；首次实现后 `py_compile`、`unittest`、`git diff --check` 均通过。

## 剩余风险

- 证据边界仍然是 `software_proof_local_mock_artifact_bundle_ingest_only`；未连接真实生产云、真实 DB/queue、真实 OSS/CDN、真实 4G/TLS 或真实机器人。
- `artifact_bundle` 只保存安全摘要和 basename，不证明真实 `route.csv`、replay JSONL、keyframe 或 evidence 文件存在、可读或可播放。
- `artifact_media_preflight` 继续是 `local_mock/not_proven` 预检，不等于真实媒体可访问，也不等于 O7 已完成真实回放。
