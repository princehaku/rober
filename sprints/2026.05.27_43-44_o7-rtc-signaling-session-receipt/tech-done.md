# O7 RTC Signaling Session Receipt

sprint_type: micro

## 实际改动

- 在 `remote_cloud_relay.py` 新增 `POST /api/o7/rtc/signaling/sessions`。
- 新增 `build_o7_rtc_signaling_session_receipt(body)`，schema 为 `trashbot.o7.rtc_signaling_session_receipt.v1`。
- endpoint 采用 bearer gate；expected token 为空时保留本地测试免 bearer 行为。
- receipt 只校验 JSON object、`robot_id`、`client_id`、`session_id`、`idempotency_key`、`offer.sdp`，只返回字段长度和短哈希摘要，不回显 SDP、token/auth/url 或 raw offer。
- receipt 固定 `blocked_not_created` 和所有 RTC、媒体、ROS2 `/tf`、硬件、控制、送达能力为 false；不触碰 command store。
- 更新 O7 RTC signaling contract 文档、session receipt 文档和 cloud-relay README。

## 验证结果

已运行通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
......................................................................................................................
----------------------------------------------------------------------
Ran 118 tests in 38.773s

OK

python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
# 无输出，退出码 0。

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/interfaces/o7_rtc_signaling_contract_api.md docs/interfaces/o7_rtc_signaling_session_receipt_api.md sprints/2026.05.27_43-44_o7-rtc-signaling-session-receipt/tech-done.md
# 无输出，退出码 0。
```

## 剩余风险

- 当前只证明 Docker/local software HTTP receipt 行为，不证明真实 WebRTC offer/answer、ICE、媒体、实时地图、ROS2 `/tf`、公网 TLS、4G、HIL 或真实送达。
