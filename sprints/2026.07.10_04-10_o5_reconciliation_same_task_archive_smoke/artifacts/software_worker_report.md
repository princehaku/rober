# Robot Software Worker Report

## 改动文件

- `onboard/scripts/o5_same_task_mission_archive_smoke.py`
- `onboard/tests/test_o5_same_task_mission_archive_smoke.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`

## 实现内容

- 新增可单独运行的本地 smoke：`o5_same_task_mission_archive_smoke.py`。
- smoke 固定使用 in-process relay、mock Nav2 proof、mock route bag pose progress、mock `route.csv` / keyframe / replay，不触发真实硬件、外网、Nav2 launch 或 `/cmd_vel`。
- smoke 主链路为：
  1. `POST /api/commands/confirm-dropoff`
  2. `POST /robots/<robot_id>/commands/<command_id>/terminal-result`
  3. `GET /api/commands/<command_id>/result?robot_id=...`
  4. `field_route_evidence_manifest.py --cloud-terminal-result-json`
  5. `POST /api/o6/archive/field-evidence`
  6. `GET /api/o6/consumer/tasks/<task_id>?include=same_task_mission_evidence_gate`
- 新增 unittest 覆盖 smoke 运行和 CLI 输出文件。
- 在 `test_remote_cloud_relay.py` 增补 reconciliation payload 中 nested `terminal_result.schema` 断言，确保 smoke 消费的是 wrapper 内的 direct terminal result 合同。
- 文档补充了 smoke 入口和证据边界：`software_proof_o5_reconciliation_same_task_archive_smoke_only`。

## 验证命令

```bash
python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py
python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check -- onboard/scripts/o5_same_task_mission_archive_smoke.py onboard/tests/test_o5_same_task_mission_archive_smoke.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/artifacts/software_worker_report.md
```

结果：

- `python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py`：通过。
- `python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke`：`Ran 2 tests in 1.180s`，`OK`。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：`Ran 166 tests in 64.457s`，`OK`。
- `git diff --check -- ...`：通过。

## 失败定位

- 当前未在本 worker 报告内记录失败；若后续回归失败，优先看：
  - reconciliation v2 是否仍返回 nested `terminal_result.schema`
  - `field_route_evidence_manifest.py --cloud-terminal-result-json` 是否继续接受 reconciliation wrapper
  - O6 `field-evidence` ingest 是否仍允许 `same_task_mission_evidence_gate` additive 回读

## 剩余风险

- 该 smoke 只证明 local/mock same-task archive/readback，不证明真实公网 HTTPS/TLS、真实 4G/SIM、真实 production DB/queue、真实 OSS/CDN、真实 live Nav2 route execution、真实 operator confirmation 或真实 delivery success。
- relay reconciliation wrapper 当前是 phone-safe 摘要；它不携带真实现场任务成功证明，只能作为同 task 软件链路的安全来源。
- 该脚本故意保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，所以不能被产品或现场误读为 live mission success。
