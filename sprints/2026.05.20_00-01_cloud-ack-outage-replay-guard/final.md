# Sprint 2026.05.20_00-01 Cloud ACK Outage Replay Guard - Final

## 1. 总结

本轮完成 `cloud_ack_outage_replay_guard`：`remote_bridge` 在本地命令已执行但 terminal ACK 上报云端失败或 ACK response malformed 时，会持久化 redacted pending ACK；worker restart / next poll 会先补发 pending ACK，补发成功后才推进 `last_terminal_ack_id` 并清理 pending ACK，从而避免重复执行本地命令和云端/本地状态分叉。

证据边界固定为 `software_proof_docker_cloud_ack_outage_replay_guard`。本轮是 Objective 5 command/status/ack 可靠性的一段 Docker/local software proof，不证明真实 4G、公网 HTTPS/TLS、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success。

## 2. 用户价值和北极星

用户价值：网络抖动或云端 ACK 上报故障后，机器人不会在重启时重复执行已经本地完成的命令，手机端也不会把“云端刚收到 ACK envelope”误看成真实送达成功。

产品北极星对齐：普通手机用户只看到稳定、可解释、可恢复的远程控制状态；复杂 ACK/cursor/replay 细节被封装在 robot/cloud contract 内，不暴露给用户。

## 3. OKR 映射和 KR 拆解

- Objective 5：云中转 + OSS/CDN 数据通路产品化。
  - KR1 command/status/ack 契约：补强 terminal ACK cursor 和 pending ACK replay。
  - KR6 4G 中断 graceful degradation：在 cloud ACK outage / malformed response 下 fail closed，并保留可恢复状态。
- Objective 4：手机用户体验与低成本量产边界。
  - Full-Stack 只读确认现有 fail-closed copy 足够，不需要新增 UI。

Objective 5 仍保持约 68%，因为本轮没有真实公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。

## 4. 核心抓手和责任人

- Robot Platform Engineer：`remote_bridge.py` pending ACK durable replay guard、targeted tests、`docs/product/remote_4g_mvp.md` 同步。
- User Touchpoint Full-Stack Engineer：mobile/web 只读语义确认，保持 `waiting_for_command_ack`、`cloud_unreachable`、`malformed_response`、`retry_hint`、`safe_phone_copy` 不等于 delivery success。
- Product Manager / OKR Owner：本 sprint 六文档 closeout、OKR 4.1、`docs/process/okr_progress_log.md`、提交推送。

## 5. 验证结果

Product closeout 复跑：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 125 tests in 64.590s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
passed
```

```text
rg -n "cloud_ack_outage_replay_guard|pending ACK|last_terminal_ack_id|software_proof_docker_cloud_ack_outage_replay_guard|delivery success|production DB/queue|4G|PRRT_kwDOSWB9286CJ3tX|Objective 5" ...
matched required implementation, docs, OKR, progress log, and sprint closeout strings
```

```text
git diff --check -- OKR.md docs/process/okr_progress_log.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/product/remote_4g_mvp.md sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard
passed
```

```text
git diff --cached --check
passed
```

## 6. OKR 收口

- Objective 5：保持约 68%。最新 sprint 更新为 `2026.05.20_00-01_cloud-ack-outage-replay-guard`。
- `docs/process/okr_progress_log.md` 已新增 2026-05-20 00-01 进度记录。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，不能因本轮 ACK replay guard 关闭。

## 7. 剩余风险

- 生产层面仍缺真实 4G/SIM、公网 HTTPS/TLS、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover、多实例一致性、queue ordering、transaction isolation、backup/recovery 和真实手机/browser 验收。
- 机器人层面仍缺 Nav2/fixed-route、WAVE ROVER、UART、HIL、真实 route/elevator field pass、dropoff/cancel completion 和 delivery success。
- PR #5 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
