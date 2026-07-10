# O6 Worker Report

## 本轮目标

把现有离线路线材料接入 O6 artifact bundle / consumer read 主路径，新增 `trashbot.o6.offline_artifact_seed_smoke.v1` 离线种子摘要，并确保同一 `task_id` 能在 archive detail 和 consumer detail 中读到 route / replay / keyframe / evidence 的软件证明小文件 probe 摘要。

## 实际改动

实际改动的文件：

- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/artifacts/o6_worker_report.md`

实现内容：

1. 新增 O6 schema 常量 `trashbot.o6.offline_artifact_seed_smoke.v1`，以及 `local_mock_offline_artifact_seed_smoke` / `software_proof_offline_artifact_seed_smoke_only` 对应 source 和 proof scope。
2. 新增离线 seed-smoke 汇总函数，把 `artifact_access_probe` 与 artifact bundle / field evidence refs 收敛成只读摘要，只保留 counts、sample basename refs、sha256 prefix、blocked_reasons、next_required_evidence、proof_boundary 和全 false 安全旗标。
3. 把该 section 挂到 archive detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest` 和 consumer detail。
4. 将 `GET /api/o6/consumer/tasks/<task_id>?include=offline_artifact_seed_smoke` 接入白名单，并让默认全量 include 自动包含该 section。
5. 补了基于仓库真实 fixture 的单测，直接用：
   - `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/route.csv`
   - `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/manifest.json`
   - `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/keyframes/001.jpg`
   - `sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/derived_replay.jsonl`
   作为 allowlist root probe 输入。

## 验证结果

已运行并通过：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

```bash
git diff --check
```

关键结果：

- `unittest` 共运行 `154` 个测试，结果 `OK`。
- 新增 seed-smoke 测试确认了 archive detail 与 consumer detail 都能读到 `offline_artifact_seed_smoke`。
- 仓库 fixture 的 allowlist probe 读到了 `route.csv`、`derived_replay.jsonl`、`001.jpg`、`manifest.json`，`readable_ref_count=4`。

## 剩余风险

- 这仍然是 `software_proof_offline_artifact_seed_smoke_only`，不证明真实 production cloud、真实 OSS/CDN、真实媒体播放、真实机器人运动或 delivery success。
- 当前实现只覆盖本地文件 allowlist probe 和离线摘要，不替代 HIL、串口、ROS2 runtime 或真实控制链路验证。

## 运行时间

2026-07-09 12:18:53 CST
