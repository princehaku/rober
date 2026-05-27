# O7 RTC Signaling Session Receipt

sprint_type: micro

## 实际改动

- 在 `remote_cloud_relay.py` 新增 `POST /api/o7/rtc/signaling/sessions`。
- 新增 `build_o7_rtc_signaling_session_receipt(body)`，schema 为 `trashbot.o7.rtc_signaling_session_receipt.v1`。
- endpoint 采用 bearer gate；expected token 为空时保留本地测试免 bearer 行为。
- receipt 只校验 JSON object、`robot_id`、`client_id`、`session_id`、`idempotency_key`、`offer.sdp`，只返回字段长度和短哈希摘要，不回显 SDP、token/auth/url 或 raw offer。
- receipt 固定 `blocked_not_created` 和所有 RTC、媒体、ROS2 `/tf`、硬件、控制、送达能力为 false；不触碰 command store。
- 更新 O7 RTC signaling contract 文档、session receipt 文档和 cloud-relay README。
- 本轮 relay consistency fix 将 `GET /api/o7/rtc-signaling/contract` 的合同状态同步到 receipt-only 现实：`signaling_endpoint.status=receipt_only_implemented`、`session_identity.status=receipt_only_validated`、`offer_answer.status=offer_receipt_only_answer_disabled`。
- `blocked_reasons` 不再声明 endpoint 未实现，改为 `rtc_signaling_receipt_only`、`real_rtc_session_not_created`、`webrtc_answer_disabled` 与 ICE/media/pose/ROS2 `/tf` 未证明；ICE、media、pose、elevator 仍保持未实现/未证明口径。
- 单测新增合同状态和 blocked reason 断言，防止后续回退到 endpoint 未实现或误宣称真实 RTC 能力。

## 验证结果

已运行通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
......................................................................................................................
----------------------------------------------------------------------
Ran 118 tests in 38.945s

OK

python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
# 无输出，退出码 0。

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/interfaces/o7_rtc_signaling_contract_api.md docs/interfaces/o7_rtc_signaling_session_receipt_api.md sprints/2026.05.27_43-44_o7-rtc-signaling-session-receipt/tech-done.md
# 无输出，退出码 0。
```

## 剩余风险

- 当前只证明 Docker/local software HTTP receipt 行为，不证明真实 WebRTC offer/answer、ICE、媒体、实时地图、ROS2 `/tf`、公网 TLS、4G、HIL 或真实送达。
