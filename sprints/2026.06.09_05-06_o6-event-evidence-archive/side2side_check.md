# O6 Event Evidence Archive Side2Side Check

## sprint_type: epic

## 对照检查

| PRD / Tech Plan 要求 | 实现状态 | 证据 |
| --- | --- | --- |
| `POST /api/o6/archive/events` | 已实现 | `remote_cloud_relay.py` 新增 `archive_store.upsert_archive_events()` 与 HTTP route |
| `GET /api/o6/archive/events` | 已实现 | 支持 `robot_id/task_id/event_type/from_ms/to_ms/limit` |
| `POST /api/o6/archive/evidence` | 已实现 | `archive_store.upsert_archive_evidence()` 只保存 ref 摘要 |
| `GET /api/o6/archive/evidence` | 已实现 | 支持 `robot_id/task_id/evidence_type/event_id/limit` |
| events 附着已有 task | 已实现 | `unknown_task` 返回 404，`unauthorized_task` 返回 403 |
| evidence 附着已有 task | 已实现 | 同上 |
| 幂等 upsert | 已实现 | `task_id + event_id`、`task_id + evidence_id` |
| 成功响应固定真实能力 false | 已实现 | `safe_to_control=false`、`delivery_success=false`、`real_cloud_db_connected=false`、`real_oss_connected=false`、`real_oss_upload_success=false` |
| GET 返回白名单字段和 summary | 已实现 | `event_summary`、`evidence_summary` 与字段裁剪 |
| evidence 不保存原始大对象 | 已实现 | `base64/raw/image/video/audio/full_log/model_response` 等 raw content fail-closed |
| task detail 兼容读回 | 已实现 | 新增测试覆盖 `GET /api/o6/archive/tasks/<task_id>` 读回 `events[]` / `evidence_refs[]` |
| 不触碰硬件/串口/launch/SSH | 已满足 | 改动文件均在授权范围内 |

## 验收证据

```text
python3 -m py_compile ...remote_cloud_relay.py ...test_remote_cloud_relay.py
exit code: 0
```

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 142 tests in 46.752s
OK
```

```text
rg keyword acceptance: passed
git diff --check: passed
```

## 用户旅程变化

Orange Pi / 上位机软件现在可以在 task 创建后持续追加路线、电梯、失败、恢复和 operator note 事件；PC/O7 后续可以按 task timeline 拉取事件和 evidence ref 摘要，做路线回放、失败复盘和标注 seed。用户触点收益是：operator 不再只能看到一次性 task snapshot，而能看到可查询、可幂等更新、不会伪装真实云能力的本地 timeline。

## 剩余风险

本轮没有真实 OSS/DB/production cloud/4G/现场采集联调。所有响应仍必须以 `proof_status=not_proven` 和固定 false 字段展示。
