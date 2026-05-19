# Sprint 2026.05.20_00-01 Cloud ACK Outage Replay Guard - Tech Done

## 1. Sprint 类型

- sprint_type: epic
- 收口时间：2026-05-20 00:19 Asia/Shanghai。
- 证据边界：`software_proof_docker_cloud_ack_outage_replay_guard`。
- Product closeout 结论：实现已落地并通过围栏验证；Objective 5 仍保持约 68%，本轮不计为真实外部云/4G/手机/生产证据。

## 2. 实际改动

Robot worker 已完成 `cloud_ack_outage_replay_guard`：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - 增加 cursor state protocol version、`pending_terminal_ack` durable state 和 `software_proof_docker_cloud_ack_outage_replay_guard` proof boundary。
  - ACK POST 失败或 malformed ACK response 时保存 redacted pending ACK，不推进 `last_terminal_ack_id`。
  - worker restart / next poll 先 replay pending ACK，成功后才推进 cursor 并清理 pending ACK。
  - pending ACK state 只保留 command id、safe ACK envelope、safe operator status subset、`robot_id`、protocol version、updated_at 和 evidence boundary。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 覆盖 ACK outage 后 pending ACK 持久化、malformed ACK response、restart replay、不重复本地执行、state redaction 和 cursor 清理。
- `docs/product/remote_4g_mvp.md`
  - 增加 `cloud_ack_outage_replay_guard` 小节，写清恢复顺序、持久化字段、清理时机和证据边界。

Full-Stack worker 只读确认：当前 mobile/web 已 fail-closed；ACK / pending ACK / `cloud_unreachable` / `malformed_response` / `retry_hint` / `safe_phone_copy` 语义不会把 ACK 接收误写成 delivery success，本轮不需要 UI 改动。

Product closeout 已补齐：

- `sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/tech-done.md`
- `sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/side2side_check.md`
- `sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 验证结果

Robot worker 已报告：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 125 tests in 64.566s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
passed
```

```text
required rg
matched proof boundary / pending ACK / cursor / risk strings
```

```text
scoped git diff --check
passed
```

Product closeout 复跑验收命令，结果写入 `final.md`。若 closeout 验证和上述 worker 结果出现差异，以 `final.md` 的最终复跑结果为准。

## 4. 偏差

- `docs/product/remote_4g_mvp.md` 已同步更新；mobile/web 无需同步改动，因为 Full-Stack 只读确认现有 fail-closed copy 已覆盖本轮风险。
- 本轮没有改变 cloud relay HTTP envelope、mobile endpoint、ROS topic、operator backend command semantics 或生产部署形态。

## 5. 剩余风险

- 本轮只证明 local worker state file + targeted unit tests 下的 ACK outage replay guard。
- 不证明真实 4G/SIM、公网 HTTPS/TLS、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover、多实例一致性、backup/recovery、真实手机/browser、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，本轮不提供真实 2D LiDAR / ToF SKU/source/procurement/material evidence。
